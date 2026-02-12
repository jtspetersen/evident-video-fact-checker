(function () {
    "use strict";

    // ── Stage definitions ──────────────────────────────────────────────
    var STAGES = [
        {
            key: "prepare_transcript",
            panel: "prepare-detail",
            steps: [
                { delay: 400, log: "Fetching YouTube transcript from https://www.youtube.com/watch?v=0fiBf-E7e0w", set: { "prepare-message": "Parsing YouTube URL..." } },
                { delay: 600, log: "YouTube: trying_captions \u2014 Looking for existing captions...", set: { "prepare-message": "Looking for existing YouTube captions..." } },
                { delay: 500, log: "YouTube: captions_found \u2014 Captions found!", set: { "prepare-message": "Captions found! Downloading transcript...", "prepare-source": "captions" } },
                { delay: 400, log: "YouTube: done \u2014 Transcript ready (19549 chars)", set: { "prepare-message": "Transcript ready (captions)", "prepare-source": "captions" } },
                { delay: 300, log: "Normalizing transcript", set: { "prepare-message": "Normalizing transcript..." } }
            ]
        },
        {
            key: "extract_claims",
            panel: "extract-detail",
            steps: [
                { delay: 300, log: "Extracting claims from transcript", set: { "extract-message": "Preparing to extract claims from 13 chunks...", "extract-total": "13" }, attr: { "extract-bar": { max: 13 } } },
                { delay: 500, log: "Extracting chunk 1/13... (0 claims so far)", set: { "extract-message": "Analyzing chunk 1 of 13...", "extract-chunk": "1" }, attr: { "extract-bar": { value: 0 } } },
                { delay: 400, log: "Chunk 1/13 done \u2014 2 new claims (2 total)", set: { "extract-message": "Chunk 1 complete \u2014 2 claims found (2 total)", "extract-chunk": "1", "extract-claims": "2" }, attr: { "extract-bar": { value: 1 } }, counter: { "cnt-claims": 2 } },
                { delay: 400, log: "Chunk 2/13 done \u2014 5 new claims (7 total)", set: { "extract-message": "Chunk 2 complete \u2014 5 claims found (7 total)", "extract-chunk": "2", "extract-claims": "7" }, attr: { "extract-bar": { value: 2 } }, counter: { "cnt-claims": 7 } },
                { delay: 400, log: "Chunk 3/13 done \u2014 5 new claims (12 total)", set: { "extract-message": "Chunk 3 complete \u2014 5 claims found (12 total)", "extract-chunk": "3", "extract-claims": "12" }, attr: { "extract-bar": { value: 3 } }, counter: { "cnt-claims": 12 } },
                { delay: 350, log: "Chunk 5/13 done \u2014 6 new claims (18 total)", set: { "extract-message": "Chunk 5 complete \u2014 6 claims found (18 total)", "extract-chunk": "5", "extract-claims": "18" }, attr: { "extract-bar": { value: 5 } }, counter: { "cnt-claims": 18 } },
                { delay: 350, log: "Chunk 8/13 done \u2014 3 new claims (21 total)", set: { "extract-message": "Chunk 8 complete \u2014 3 claims found (21 total)", "extract-chunk": "8", "extract-claims": "21" }, attr: { "extract-bar": { value: 8 } }, counter: { "cnt-claims": 21 } },
                { delay: 350, log: "Chunk 13/13 done \u2014 4 new claims (25 total)", set: { "extract-message": "Chunk 13 complete \u2014 4 claims found (25 total)", "extract-chunk": "13", "extract-claims": "25" }, attr: { "extract-bar": { value: 13 } }, counter: { "cnt-claims": 25 } },
                { delay: 300, log: "Claims extracted: 25", set: { "extract-message": "Extraction complete" } },
                // Consolidation
                { delay: 400, log: "Consolidating claims (dedup + narrative groups)", set: { "consolidate-message": "Analyzing 25 claims for duplicates and narrative groups..." }, style: { "consolidate-stats": { display: "block" } } },
                { delay: 600, log: "Consolidation: 2 duplicates removed, 2 narrative groups", set: { "consolidate-message": "Consolidation complete \u2014 2 duplicates removed, 2 narrative groups", "consolidate-dupes": "2", "consolidate-groups": "2" }, counter: { "cnt-claims": 23, "cnt-groups": 2 } }
            ]
        },
        {
            key: "review_claims",
            redirect: "review.html"
        },
        {
            key: "gather_evidence",
            panel: "retrieve-detail",
            steps: [
                { delay: 300, log: "Generating search queries (3 per claim, 3 workers)...", set: { "retrieve-message": "Generating search queries...", "retrieve-total": "23" }, attr: { "retrieve-bar": { max: 23 } } },
                { delay: 500, log: "Generated search queries for 23 claims", set: { "retrieve-message": "Search queries ready" } },
                { delay: 400, log: "Searching evidence for claim 1/23 (C001)...", set: { "retrieve-message": "Searching for evidence \u2014 claim 1/23 (C001)...", "retrieve-claim-idx": "1" }, attr: { "retrieve-bar": { value: 0 } } },
                { delay: 350, log: "Claim 1/23 done \u2014 1 sources, 4 snippets, 2 failures", set: { "retrieve-message": "Claim 1/23 done \u2014 4 snippets matched", "retrieve-claim-idx": "1", "retrieve-sources": "1", "retrieve-snippets": "4", "retrieve-failures": "2" }, attr: { "retrieve-bar": { value: 1 } }, counter: { "cnt-sources": 1, "cnt-snippets": 4, "cnt-failures": 2 } },
                { delay: 350, log: "Claim 2/23 done \u2014 4 sources, 16 snippets, 3 failures", set: { "retrieve-claim-idx": "2", "retrieve-sources": "4", "retrieve-snippets": "16", "retrieve-failures": "3" }, attr: { "retrieve-bar": { value: 2 } }, counter: { "cnt-sources": 4, "cnt-snippets": 16, "cnt-failures": 3 } },
                { delay: 300, log: "Claim 7/23 done \u2014 22 sources, 86 snippets, 13 failures", set: { "retrieve-claim-idx": "7", "retrieve-sources": "22", "retrieve-snippets": "86", "retrieve-failures": "13" }, attr: { "retrieve-bar": { value: 7 } }, counter: { "cnt-sources": 22, "cnt-snippets": 86, "cnt-failures": 13 } },
                { delay: 300, log: "Claim 13/23 done \u2014 51 sources, 200 snippets, 16 failures", set: { "retrieve-claim-idx": "13", "retrieve-sources": "51", "retrieve-snippets": "200", "retrieve-failures": "16" }, attr: { "retrieve-bar": { value: 13 } }, counter: { "cnt-sources": 51, "cnt-snippets": 200, "cnt-failures": 16 } },
                { delay: 300, log: "Claim 23/23 done \u2014 62 sources, 244 snippets, 18 failures", set: { "retrieve-claim-idx": "23", "retrieve-sources": "62", "retrieve-snippets": "244", "retrieve-failures": "18" }, attr: { "retrieve-bar": { value: 23 } }, counter: { "cnt-sources": 62, "cnt-snippets": 244, "cnt-failures": 18 } }
            ]
        },
        {
            key: "check_claims",
            panel: "verify-detail",
            steps: [
                { delay: 300, log: "Checking claims against evidence", set: { "verify-message": "Starting parallel verification...", "verify-total": "23" }, attr: { "verify-bar": { max: 23 } } },
                { delay: 500, log: "Verified 1/23 claim_id=C002 rating=FALSE conf=0.9", set: { "verify-message": "Checked 1 of 23 claims...", "verify-current": "1" }, attr: { "verify-bar": { value: 1 } }, counter: { "cnt-verdicts": 1 } },
                { delay: 400, log: "Verified 2/23 claim_id=C003 rating=INSUFFICIENT EVIDENCE conf=0.4", set: { "verify-message": "Checked 2 of 23 claims...", "verify-current": "2" }, attr: { "verify-bar": { value: 2 } }, counter: { "cnt-verdicts": 2 } },
                { delay: 400, log: "Verified 4/23 claim_id=C004 rating=TRUE conf=0.9", set: { "verify-message": "Checked 4 of 23 claims...", "verify-current": "4" }, attr: { "verify-bar": { value: 4 } }, counter: { "cnt-verdicts": 4 } },
                { delay: 350, log: "Verified 8/23 claim_id=C006 rating=FALSE conf=0.9", set: { "verify-message": "Checked 8 of 23 claims...", "verify-current": "8" }, attr: { "verify-bar": { value: 8 } }, counter: { "cnt-verdicts": 8 } },
                { delay: 350, log: "Verified 12/23 claim_id=C012 rating=FALSE conf=0.9", set: { "verify-message": "Checked 12 of 23 claims...", "verify-current": "12" }, attr: { "verify-bar": { value: 12 } }, counter: { "cnt-verdicts": 12 } },
                { delay: 350, log: "Verified 18/23 claim_id=C019 rating=INSUFFICIENT EVIDENCE conf=0.3", set: { "verify-message": "Checked 18 of 23 claims...", "verify-current": "18" }, attr: { "verify-bar": { value: 18 } }, counter: { "cnt-verdicts": 18 } },
                { delay: 350, log: "Verified 23/23 claim_id=C015 rating=FALSE conf=0.85", set: { "verify-message": "Checked 23 of 23 claims...", "verify-current": "23" }, attr: { "verify-bar": { value: 23 } }, counter: { "cnt-verdicts": 23 } },
                { delay: 400, log: "Verifying 2 narrative groups", set: { "verify-message": "Verifying narrative groups..." } },
                { delay: 400, log: "Group G001: MISLEADING (confidence=0.7)", set: { "verify-message": "Group G001 verified \u2014 MISLEADING" } },
                { delay: 400, log: "Group G002: MISLEADING (confidence=0.9)", set: { "verify-message": "Group G002 verified \u2014 MISLEADING" } }
            ]
        },
        {
            key: "fact_check_summary",
            steps: [
                { delay: 300, log: "Generating fact-check summary" },
                { delay: 500, log: "Aggregating verdict scorecard" },
                { delay: 500, log: "Writing fact-check report..." },
                { delay: 600, log: "Report complete!" },
                { delay: 300, log: "RUN COMPLETE" }
            ],
            endRedirect: "report.html"
        }
    ];

    var STAGE_LABELS = {
        prepare_transcript: "Prepare Transcript",
        extract_claims: "Extract Claims",
        review_claims: "Review Claims",
        gather_evidence: "Gather Evidence",
        check_claims: "Check Claims",
        fact_check_summary: "Fact-Check Summary"
    };

    // ── State ──────────────────────────────────────────────────────────
    var params = new URLSearchParams(window.location.search);
    var afterReview = params.get("after") === "review";

    var currentStageIdx = afterReview ? 3 : 0; // Skip to gather_evidence after review
    var isPlaying = false;

    var nextBtn = document.getElementById("next-btn");
    var statusBadge = document.getElementById("status-badge");
    var logStream = document.getElementById("log-stream");
    var allPanels = document.querySelectorAll(".stage-detail");
    var logStarted = false;

    // ── Helpers ─────────────────────────────────────────────────────────

    function addLog(text) {
        if (!logStarted) {
            logStream.innerHTML = "";
            logStarted = true;
        }
        var div = document.createElement("div");
        div.className = "log-line";
        div.textContent = text;
        logStream.appendChild(div);
        // Cap at 50 visible lines
        while (logStream.children.length > 50) {
            logStream.removeChild(logStream.firstChild);
        }
        logStream.scrollTop = logStream.scrollHeight;
    }

    function hideAllPanels() {
        allPanels.forEach(function (p) {
            p.classList.remove("visible");
        });
    }

    function showPanel(id) {
        var p = document.getElementById(id);
        if (p) p.classList.add("visible");
    }

    /**
     * Smoothly animate a counter element from its current value to `target`.
     * Ticks happen over ~200ms total, with up to 15 discrete steps.
     */
    function animateCounter(id, target) {
        var el = document.getElementById(id);
        if (!el) return;
        var current = parseInt(el.textContent, 10) || 0;
        if (current === target) return;
        var diff = target - current;
        var totalSteps = Math.min(Math.abs(diff), 15);
        var stepTime = Math.max(Math.round(200 / totalSteps), 10);
        var i = 0;
        function tick() {
            i++;
            var val = Math.round(current + diff * (i / totalSteps));
            el.textContent = val;
            if (i < totalSteps) {
                setTimeout(tick, stepTime);
            }
        }
        tick();
    }

    /**
     * Apply a single step's effects (log, set text, set attributes, set styles,
     * animate counters).
     */
    function applyStep(step) {
        if (step.log) addLog(step.log);

        if (step.set) {
            for (var id in step.set) {
                if (step.set.hasOwnProperty(id)) {
                    var el = document.getElementById(id);
                    if (el) el.textContent = step.set[id];
                }
            }
        }

        if (step.attr) {
            for (var id in step.attr) {
                if (step.attr.hasOwnProperty(id)) {
                    var el = document.getElementById(id);
                    if (el) {
                        var attrs = step.attr[id];
                        for (var a in attrs) {
                            if (attrs.hasOwnProperty(a)) {
                                el[a] = attrs[a];
                            }
                        }
                    }
                }
            }
        }

        if (step.style) {
            for (var id in step.style) {
                if (step.style.hasOwnProperty(id)) {
                    var el = document.getElementById(id);
                    if (el) {
                        var props = step.style[id];
                        for (var prop in props) {
                            if (props.hasOwnProperty(prop)) {
                                el.style[prop] = props[prop];
                            }
                        }
                    }
                }
            }
        }

        if (step.counter) {
            for (var id in step.counter) {
                if (step.counter.hasOwnProperty(id)) {
                    animateCounter(id, step.counter[id]);
                }
            }
        }
    }

    // ── Post-review initialization ──────────────────────────────────────
    if (afterReview) {
        // Mark first three stages as completed
        ["prepare_transcript", "extract_claims", "review_claims"].forEach(function (s) {
            var el = document.getElementById("stage-" + s);
            if (el) el.classList.add("completed");
        });
        // Set counters to post-review values
        document.getElementById("cnt-claims").textContent = "23";
        document.getElementById("cnt-groups").textContent = "2";
        // Set button label
        nextBtn.textContent = "Continue to Gather Evidence";
        // Prime the log
        logStarted = true;
        logStream.innerHTML = "";
        addLog("Review complete \u2014 23 claims kept");
        addLog('Click "Continue to Gather Evidence" to proceed');
    }

    // ── Engine: play the current stage ──────────────────────────────────

    function playCurrentStage() {
        if (currentStageIdx >= STAGES.length) return;
        var stage = STAGES[currentStageIdx];

        // ── Redirect stages (e.g. review) ──
        if (stage.redirect) {
            var el = document.getElementById("stage-" + stage.key);
            if (el) el.classList.add("active");
            addLog("Redirecting to claim review...");
            statusBadge.textContent = "review";
            statusBadge.className = "badge badge-review";
            setTimeout(function () {
                window.location.href = stage.redirect;
            }, 800);
            return;
        }

        // ── Normal stages ──
        var stageEl = document.getElementById("stage-" + stage.key);
        if (stageEl) {
            stageEl.classList.remove("completed");
            stageEl.classList.add("active");
        }
        hideAllPanels();
        if (stage.panel) showPanel(stage.panel);

        isPlaying = true;
        nextBtn.disabled = true;
        nextBtn.setAttribute("aria-busy", "true");
        nextBtn.textContent = "Running...";

        var steps = stage.steps || [];
        var stepIdx = 0;

        function nextStep() {
            if (stepIdx >= steps.length) {
                // ── Stage complete ──
                if (stageEl) {
                    stageEl.classList.remove("active");
                    stageEl.classList.add("completed");
                }
                hideAllPanels();
                isPlaying = false;
                nextBtn.disabled = false;
                nextBtn.removeAttribute("aria-busy");
                currentStageIdx++;

                // If this stage has an end-redirect, morph button into "View Report"
                if (stage.endRedirect) {
                    addLog("Redirecting to report...");
                    statusBadge.textContent = "done";
                    statusBadge.className = "badge badge-done";
                    nextBtn.textContent = "View Report";
                    nextBtn.onclick = function () {
                        window.location.href = stage.endRedirect;
                    };
                    return;
                }

                // Otherwise, set button text for the next stage
                if (currentStageIdx < STAGES.length) {
                    var nextKey = STAGES[currentStageIdx].key;
                    if (STAGES[currentStageIdx].redirect) {
                        nextBtn.textContent = "Review Claims";
                    } else {
                        var label = STAGE_LABELS[nextKey] || nextKey;
                        nextBtn.textContent = "Continue to " + label;
                    }
                }
                return;
            }

            // Apply this step then schedule the next
            var step = steps[stepIdx];
            applyStep(step);
            var delay = step.delay || 300;
            stepIdx++;
            setTimeout(nextStep, delay);
        }

        nextStep();
    }

    // ── Button handler ──────────────────────────────────────────────────
    nextBtn.addEventListener("click", function () {
        if (isPlaying) return;
        playCurrentStage();
    });
})();
