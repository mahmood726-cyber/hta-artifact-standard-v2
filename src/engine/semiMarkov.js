/**
 * Semi-Markov Cohort Engine
 * Extends Markov with sojourn-time (time-in-state) dependent transitions.
 *
 * Uses tunnel states internally to track time-in-state for each sub-cohort,
 * then aggregates back to named states for output.
 *
 * Sojourn distribution types:
 *   - constant: standard Markov (rate-based, time-independent)
 *   - weibull:  h(t) = (shape/scale) * (t/scale)^(shape-1)
 *   - gamma:    hazard from gamma PDF / survival at time-in-state t
 *   - lognormal: hazard from lognormal PDF / survival at time-in-state t
 *
 * Reference: RFC-005 Determinism Contract
 */

'use strict';

// ---------- Dependency resolution ----------

const _PCG32Ref = (function() {
    if (typeof globalThis !== 'undefined' && globalThis.PCG32) return globalThis.PCG32;
    if (typeof require === 'function') { try { return require('../utils/pcg32').PCG32; } catch(e) {} }
    return null;
})();

const KahanSumRef = (function() {
    if (typeof globalThis !== 'undefined' && globalThis.KahanSum) return globalThis.KahanSum;
    if (typeof require === 'function') { try { return require('../utils/kahan').KahanSum; } catch(e) {} }
    return null;
})();

// ---------- Math helpers ----------

/**
 * Gamma function via Lanczos approximation (for PDF computation).
 */
function _gammaFunction(z) {
    // Poles at 0, -1, -2, ... where sin(PI*z)=0 would cause division by zero
    if (z <= 0 && z === Math.floor(z)) return Infinity;
    if (z < 0.5) {
        return Math.PI / (Math.sin(Math.PI * z) * _gammaFunction(1 - z));
    }
    z -= 1;
    const g = 7;
    const c = [
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7
    ];
    let x = c[0];
    for (let i = 1; i < g + 2; i++) {
        x += c[i] / (z + i);
    }
    const t = z + g + 0.5;
    return Math.sqrt(2 * Math.PI) * Math.pow(t, z + 0.5) * Math.exp(-t) * x;
}

/**
 * Lower incomplete gamma function via series expansion.
 * P(a, x) = gamma_inc(a,x) / Gamma(a)
 */
function lowerIncompleteGamma(a, x) {
    if (x < 0) return 0;
    if (x === 0) return 0;
    let sum = 0;
    let term = 1.0 / a;
    sum = term;
    for (let n = 1; n < 200; n++) {
        term *= x / (a + n);
        sum += term;
        if (Math.abs(term) < 1e-14 * Math.abs(sum)) break;
    }
    return sum * Math.exp(-x + a * Math.log(x) - logGamma(a));
}

/**
 * Log-gamma (Stirling-based for simplicity; Lanczos for accuracy).
 */
function logGamma(z) {
    if (z < 0.5) {
        return Math.log(Math.PI / Math.sin(Math.PI * z)) - logGamma(1 - z);
    }
    z -= 1;
    const g = 7;
    const c = [
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7
    ];
    let x = c[0];
    for (let i = 1; i < g + 2; i++) {
        x += c[i] / (z + i);
    }
    const t = z + g + 0.5;
    return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
}

/**
 * Standard normal PDF.
 */
function _normalPDF(x) {
    return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
}

/**
 * Standard normal CDF (Abramowitz & Stegun 7.1.26 via erf).
 */
function normalCDF(x) {
    if (x < -8) return 0;
    if (x > 8) return 1;
    const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741;
    const a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
    let sign = 1;
    if (x < 0) { sign = -1; x = -x; }
    const xErf = x / Math.sqrt(2);
    const t = 1.0 / (1.0 + p * xErf);
    const erfApprox = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-xErf * xErf);
    return 0.5 * (1.0 + sign * erfApprox);
}

// ---------- Named Constants ----------

/** Maximum hazard rate cap to prevent numerical overflow (P2-9). */
const MAX_HAZARD_CAP = 100;

// ---------- SemiMarkovEngine ----------

class SemiMarkovEngine {
    /**
     * @param {Object} options
     * @param {number} [options.maxCycles=100]
     * @param {number} [options.tolerance=1e-9]
     * @param {number} [options.cohortSize=1000]
     * @param {number} [options.seed=12345]
     */
    constructor(options) {
        options = options || {};
        this.maxCycles = Math.min(options.maxCycles != null ? options.maxCycles : 100, 10000);
        this.tolerance = options.tolerance != null ? options.tolerance : 1e-9;
        this.cohortSize = options.cohortSize != null ? options.cohortSize : 1000;
        this.seed = options.seed != null ? options.seed : 12345;
    }

    /**
     * Convert instantaneous hazard rate to cycle transition probability.
     * p = 1 - exp(-h * cycleLength)
     * @param {number} hazard - Instantaneous hazard rate
     * @param {number} [cycleLength=1] - Cycle length in time units
     * @returns {number} Probability in [0, 1]
     */
    hazardToProb(hazard, cycleLength) {
        if (cycleLength == null) cycleLength = 1;
        if (hazard <= 0) return 0;
        const p = 1 - Math.exp(-hazard * cycleLength);
        return Math.min(Math.max(p, 0), 1);
    }

    /**
     * Compute hazard at given time-in-state for a transition specification.
     * @param {Object} transition - Transition spec with type, shape, scale, etc.
     * @param {number} timeInState - Time spent in current state (cycles, >=1)
     * @returns {number} Instantaneous hazard rate
     */
    sojournHazard(transition, timeInState) {
        if (!transition || !transition.type) {
            throw new Error('Invalid transition specification');
        }
        const t = Math.max(timeInState, 1e-10); // avoid division by zero

        switch (transition.type) {
            case 'constant':
                return transition.rate;

            case 'weibull': {
                // h(t) = (shape/scale) * (t/scale)^(shape-1)
                const k = transition.shape;
                const lam = transition.scale;
                return (k / lam) * Math.pow(t / lam, k - 1);
            }

            case 'gamma': {
                // Gamma hazard = f(t) / S(t)
                // f(t) = t^(a-1) * exp(-t/b) / (b^a * Gamma(a))
                // S(t) = 1 - P(a, t/b)  where P is regularized lower incomplete gamma
                const a = transition.shape;
                const b = transition.scale;
                const logPdf = (a - 1) * Math.log(t) - t / b - a * Math.log(b) - logGamma(a);
                const pdf = Math.exp(logPdf);
                const cdf = lowerIncompleteGamma(a, t / b);
                const survival = 1 - cdf;
                if (survival < 1e-15) return MAX_HAZARD_CAP; // effectively certain transition
                return pdf / survival;
            }

            case 'lognormal': {
                // Lognormal hazard = f(t) / S(t)
                // f(t) = (1/(t * sigma * sqrt(2pi))) * exp(-(log(t)-mu)^2 / (2*sigma^2))
                // S(t) = 1 - Phi((log(t) - mu) / sigma)
                const mu = transition.meanlog != null ? transition.meanlog : Math.log(transition.scale);
                const sigma = transition.sdlog != null ? transition.sdlog : transition.shape;
                const z = (Math.log(t) - mu) / sigma;
                const pdf_val = Math.exp(-0.5 * z * z) / (t * sigma * Math.sqrt(2 * Math.PI));
                const cdf_val = normalCDF(z);
                const surv = 1 - cdf_val;
                if (surv < 1e-15) return MAX_HAZARD_CAP;
                return pdf_val / surv;
            }

            default:
                throw new Error('Unknown transition type: ' + transition.type);
        }
    }

    /**
     * Determine whether a transition spec is sojourn-dependent (time-in-state).
     */
    _isSojournDependent(transition) {
        return transition.type !== 'constant';
    }

    /**
     * Validate the config object before running the model.
     * @param {Object} config
     * @throws {Error} on invalid configuration
     */
    _validateConfig(config) {
        const validTypes = ['constant', 'weibull', 'gamma', 'lognormal'];

        if (!config.states || !Array.isArray(config.states) || config.states.length === 0) {
            throw new Error('Config validation: states must be a non-empty array');
        }

        if (config.initial) {
            let sum = 0;
            for (let i = 0; i < config.initial.length; i++) {
                sum += config.initial[i];
            }
            if (Math.abs(sum - 1.0) > 0.01) {
                throw new Error('Config validation: initial distribution must sum to ~1.0 (got ' + sum + ')');
            }
        }

        if (config.timeHorizon != null && config.timeHorizon <= 0) {
            throw new Error('Config validation: timeHorizon must be positive');
        }

        if (config.transitions) {
            for (const key in config.transitions) {
                if (!config.transitions.hasOwnProperty(key)) continue;

                if (key.indexOf('->') === -1) {
                    throw new Error('Config validation: transition key must contain "->": ' + key);
                }

                const spec = config.transitions[key];
                if (!spec || !spec.type) {
                    throw new Error('Config validation: transition must have a type: ' + key);
                }

                if (validTypes.indexOf(spec.type) === -1) {
                    throw new Error('Config validation: invalid transition type "' + spec.type + '" for ' + key + '. Valid types: ' + validTypes.join(', '));
                }

                if (spec.type === 'constant') {
                    if (spec.rate == null || spec.rate < 0) {
                        throw new Error('Config validation: constant rate must be >= 0 for ' + key);
                    }
                }

                if (spec.type === 'weibull' || spec.type === 'gamma') {
                    if (spec.shape == null || spec.shape <= 0) {
                        throw new Error('Config validation: ' + spec.type + ' shape must be > 0 for ' + key);
                    }
                    if (spec.scale == null || spec.scale <= 0) {
                        throw new Error('Config validation: ' + spec.type + ' scale must be > 0 for ' + key);
                    }
                }
            }
        }
    }

    /**
     * Run the semi-Markov cohort model.
     *
     * @param {Object} config
     * @param {string[]} config.states - State names
     * @param {number[]} config.initial - Initial distribution (sums to 1)
     * @param {Object} config.transitions - Keyed 'From->To': {type, shape, scale, rate, ...}
     * @param {Object} config.costs - State costs (per cycle)
     * @param {Object} config.utilities - State utilities (QALYs per cycle)
     * @param {number} config.timeHorizon - Number of cycles to simulate
     * @param {number} [config.discountRate=0.035] - Annual discount rate (fallback for both costs and outcomes)
     * @param {number} [config.discountRateCosts] - Discount rate for costs (overrides discountRate)
     * @param {number} [config.discountRateOutcomes] - Discount rate for outcomes/QALYs (overrides discountRate)
     * @param {number} [config.cycleLength=1] - Cycle length
     * @param {boolean} [config.halfCycleCorrection=false] - Apply trapezoidal half-cycle correction
     * @returns {Object} Results: stateTrace, totalCosts, totalQALYs, perCycle, sojournStats
     */
    run(config) {
        this._validateConfig(config);

        const states = config.states;
        const nStates = states.length;
        const timeHorizon = config.timeHorizon || this.maxCycles;
        const discountRate = config.discountRate != null ? config.discountRate : 0.035;
        const discountRateCosts = config.discountRateCosts != null ? config.discountRateCosts : discountRate;
        const discountRateOutcomes = config.discountRateOutcomes != null ? config.discountRateOutcomes : discountRate;
        const cycleLength = config.cycleLength != null ? config.cycleLength : 1;
        const halfCycleCorrection = config.halfCycleCorrection || false;
        const maxTunnel = Math.min(timeHorizon, this.maxCycles);
        const costs = config.costs || {};
        const utilities = config.utilities || {};

        // Parse transitions: identify which state pairs are sojourn-dependent
        const transitionMap = {}; // key: 'fromIdx->toIdx', value: transition spec
        const hasSojourn = new Array(nStates).fill(false); // does this state have sojourn-dependent exits?

        for (const key in config.transitions) {
            if (!config.transitions.hasOwnProperty(key)) continue;
            const parts = key.split('->');
            const fromName = parts[0].trim();
            const toName = parts[1].trim();
            const fromIdx = states.indexOf(fromName);
            const toIdx = states.indexOf(toName);
            if (fromIdx < 0 || toIdx < 0) {
                throw new Error('Unknown state in transition: ' + key);
            }
            const spec = config.transitions[key];
            transitionMap[fromIdx + '->' + toIdx] = spec;
            if (this._isSojournDependent(spec)) {
                hasSojourn[fromIdx] = true;
            }
        }

        // Build tunnel state structure
        // For states with sojourn-dependent exits, we create tunnel[state][timeInState] sub-cohorts
        // tunnelPop[stateIdx][timeInState] = proportion of cohort in that tunnel
        // P2-2: Pre-allocate two sets of buffers and swap, instead of allocating every cycle
        let tunnelPop = [];
        let tunnelPopSwap = []; // second buffer for double-buffering
        for (let s = 0; s < nStates; s++) {
            const len = hasSojourn[s] ? (maxTunnel + 1) : 1;
            tunnelPop[s] = new Float64Array(len);
            tunnelPopSwap[s] = new Float64Array(len);
        }

        // Set initial distribution
        const initial = config.initial;
        for (let s = 0; s < nStates; s++) {
            tunnelPop[s][0] = initial[s] || 0;
        }

        // Identify absorbing states (no transitions out)
        const isAbsorbing = new Array(nStates).fill(true);
        for (const key in transitionMap) {
            const fromIdx = parseInt(key.split('->')[0]);
            isAbsorbing[fromIdx] = false;
        }

        // State trace: stateTrace[cycle][stateIdx] = proportion in state
        const stateTrace = [];
        const perCycle = [];
        const _KahanClass = KahanSumRef || { sum: function(arr) { let s=0; for(let i=0;i<arr.length;i++) s+=arr[i]; return s; } };

        // Accumulators for sojourn stats
        const sojournTimeSum = new Float64Array(nStates);
        const sojournWeightSum = new Float64Array(nStates);

        // Record initial state
        const initialAgg = new Float64Array(nStates);
        for (let s = 0; s < nStates; s++) {
            let total = 0;
            for (let t = 0; t < tunnelPop[s].length; t++) {
                total += tunnelPop[s][t];
            }
            initialAgg[s] = total;
        }
        stateTrace.push(Array.from(initialAgg));

        // Store previous cycle's aggregated population for half-cycle correction
        let prevAggPop = Array.from(initialAgg);

        // Simulate cycles
        for (let cycle = 0; cycle < timeHorizon; cycle++) {
            const discountFactorCosts = 1.0 / Math.pow(1 + discountRateCosts, cycle);
            const discountFactorOutcomes = 1.0 / Math.pow(1 + discountRateOutcomes, cycle);

            // Compute aggregated state proportions for cost/utility calculation
            const aggPop = new Float64Array(nStates);
            for (let s = 0; s < nStates; s++) {
                let total = 0;
                for (let t = 0; t < tunnelPop[s].length; t++) {
                    total += tunnelPop[s][t];
                }
                aggPop[s] = total;
            }

            // Compute per-cycle costs and QALYs
            let cycleCost = 0;
            let cycleQaly = 0;
            for (let s = 0; s < nStates; s++) {
                const stateName = states[s];
                const c = costs[stateName] != null ? costs[stateName] : 0;
                const u = utilities[stateName] != null ? utilities[stateName] : 0;
                // Half-cycle correction: trapezoidal average of current and previous cycle populations
                const effectivePop = halfCycleCorrection ? 0.5 * (aggPop[s] + prevAggPop[s]) : aggPop[s];
                cycleCost += effectivePop * c;
                cycleQaly += effectivePop * u;
            }
            perCycle.push({
                cycle: cycle,
                costs: cycleCost * discountFactorCosts,
                qalys: cycleQaly * discountFactorOutcomes,
                stateProportions: Array.from(aggPop)
            });

            // Transition: build new tunnel populations (P2-2: reuse pre-allocated swap buffers)
            const newTunnelPop = tunnelPopSwap;
            for (let s = 0; s < nStates; s++) {
                newTunnelPop[s].fill(0);
            }

            // Process each state
            for (let fromS = 0; fromS < nStates; fromS++) {
                if (isAbsorbing[fromS]) {
                    // Absorbing: all sub-cohorts stay
                    for (let t = 0; t < tunnelPop[fromS].length; t++) {
                        if (tunnelPop[fromS][t] > 0) {
                            const newT = hasSojourn[fromS] ? Math.min(t + 1, maxTunnel) : 0;
                            newTunnelPop[fromS][newT] += tunnelPop[fromS][t];
                        }
                    }
                    continue;
                }

                // For each tunnel slot in this state
                for (let t = 0; t < tunnelPop[fromS].length; t++) {
                    const pop = tunnelPop[fromS][t];
                    if (pop < 1e-15) continue;

                    const timeInState = hasSojourn[fromS] ? (t + 1) : 1; // time in state (1-based)

                    // Collect sojourn stats
                    sojournTimeSum[fromS] += pop * timeInState;
                    sojournWeightSum[fromS] += pop;

                    // Compute transition probabilities using correct competing risks decomposition:
                    // Sum all hazards first, compute total transition probability, then allocate proportionally.
                    const transHazards = []; // [{toIdx, hazard}]
                    let totalHazard = 0;

                    for (const key2 in transitionMap) {
                        const parts2 = key2.split('->');
                        const fIdx = parseInt(parts2[0]);
                        const tIdx = parseInt(parts2[1]);
                        if (fIdx !== fromS) continue;

                        const spec = transitionMap[key2];
                        const hazard = this.sojournHazard(spec, timeInState);
                        transHazards.push({ toIdx: tIdx, hazard: hazard });
                        totalHazard += hazard;
                    }

                    // Correct competing risks: total probability from combined hazard, then proportional allocation
                    let totalTransProb = (totalHazard > 0) ? (1 - Math.exp(-totalHazard * cycleLength)) : 0;
                    totalTransProb = Math.min(Math.max(totalTransProb, 0), 1);

                    const transProbs = [];
                    for (let i = 0; i < transHazards.length; i++) {
                        const allocProb = (totalHazard > 0) ? (transHazards[i].hazard / totalHazard) * totalTransProb : 0;
                        transProbs.push({ toIdx: transHazards[i].toIdx, prob: allocProb });
                    }

                    // Distribute population
                    const stayProp = pop * (1 - totalTransProb);
                    const newTStay = hasSojourn[fromS] ? Math.min(t + 1, maxTunnel) : 0;
                    newTunnelPop[fromS][newTStay] += stayProp;

                    for (let i = 0; i < transProbs.length; i++) {
                        const tp = transProbs[i];
                        const movePop = pop * tp.prob;
                        // Arriving in new state at time-in-state = 0
                        newTunnelPop[tp.toIdx][0] += movePop;
                    }
                }
            }

            // P2-2: Swap buffers — old tunnelPop becomes the swap for next cycle
            const tmpPop = tunnelPop;
            tunnelPop = newTunnelPop;
            tunnelPopSwap = tmpPop;

            // Record state trace after transition
            const cycleAgg = new Float64Array(nStates);
            for (let s = 0; s < nStates; s++) {
                let total = 0;
                for (let tt = 0; tt < tunnelPop[s].length; tt++) {
                    total += tunnelPop[s][tt];
                }
                cycleAgg[s] = total;
            }
            stateTrace.push(Array.from(cycleAgg));

            // Update previous population for half-cycle correction
            prevAggPop = Array.from(aggPop);
        }

        // Compute totals
        let totalCosts = 0;
        let totalQALYs = 0;
        for (let i = 0; i < perCycle.length; i++) {
            totalCosts += perCycle[i].costs;
            totalQALYs += perCycle[i].qalys;
        }

        // Compute sojourn stats
        const sojournStats = {};
        for (let s = 0; s < nStates; s++) {
            const meanTime = sojournWeightSum[s] > 0 ? sojournTimeSum[s] / sojournWeightSum[s] : 0;
            sojournStats[states[s]] = {
                meanTimeInState: meanTime
            };
        }

        return {
            stateTrace: stateTrace,
            totalCosts: totalCosts,
            totalQALYs: totalQALYs,
            perCycle: perCycle,
            sojournStats: sojournStats
        };
    }
}

// ---------- Export ----------

if (typeof window !== 'undefined') {
    window.SemiMarkovEngine = SemiMarkovEngine;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SemiMarkovEngine };
}
