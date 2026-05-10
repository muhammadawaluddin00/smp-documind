# Interview Prep — SMP Technology AI/ML Engineer Intern

A working cheat sheet built specifically for the interview loop. Treat this as your script — read it, mark up the parts that ring true to your own background, and rehearse.

## 30-second elevator pitch

> "I built **SMP DocuMind**, an end-to-end Document Q&A Assistant that answers questions over an internal knowledge base with grounded citations. It's three services — a Next.js dashboard, a typed Express gateway, and a Python ML service running a hybrid retrieval pipeline — wired up with a 50-question evaluation suite that scores answer relevance, retrieval hit-rate, and citation faithfulness on every run. I built it specifically to map onto the AI/ML Engineer Intern job description, so every bullet on the JD has a concrete piece of code I can point to."

## 90-second deeper pitch

> "The problem I picked is the one most internal AI assistants actually face: people ask questions, the model hallucinates, and you have no way to tell. So I built RAG with three guardrails — a hybrid retriever combining sentence-transformers and BM25, a 0.30 fused-score abstention gate, and an evaluation harness running on every change. The production-mode benchmark hits 99.4% mean answer relevance and 100% retrieval hit-rate across 50 ground-truth questions. The p95 latency landed at 2.5 seconds, just over the SLO from the product spec, which the dashboard surfaces as a warning — that's exactly the kind of finding I'd want my code to flag automatically. The whole thing is documented well enough for someone else to onboard from the README, and the brand is tokenised so it can be re-skinned to match SMP in five minutes."

## The JD ↔ project map

Use this table during the interview when they ask "tell me about your experience with X". You can always point to a concrete file.

| JD requirement | Where it lives in DocuMind |
|---|---|
| Python · NumPy · Pandas · scikit-learn · PyTorch | `ml-service/rag_pipeline.py` (numpy, sklearn TF-IDF), `ml-service/evaluation.py` (numpy aggregations), sentence-transformers pulls in PyTorch |
| GenAI tools (OpenAI, Hugging Face, LangChain, LlamaIndex) | OpenAI client in `_generate_openai`, sentence-transformers (HF) for embeddings, LangChain in `requirements.txt` for chunking |
| Build chatbots / AI assistants | The whole project — see `frontend/app/chat/page.tsx` for the chat UI |
| Data preprocessing & feature extraction | Chunking pipeline (~420 token windows, 60 token overlap), TF-IDF vectoriser in lite mode |
| Model evaluation | `ml-service/evaluation.py` + 50-question suite + `docs/MODEL_EVALUATION.md` |
| Literature review & benchmarking | Two benchmark runs (lite + production-sim) for reproducibility, MODEL_EVALUATION.md cites the RAGAS triad |
| Deployment integration with engineers | Three-service architecture — TS gateway is the integration surface |
| Document development processes | The `docs/` folder you are reading right now |
| Prompt engineering | `data/synthetic/documents/DOC-009.md` is the style guide; system prompt in `_generate_openai` |

## Likely questions and how to answer them

### "Walk me through your project."

Open with the 30-second pitch above, then offer to go deep in one of three directions: (a) the architecture, (b) the evaluation, (c) a specific design decision. Let them pick. This signals that you can read the room instead of monologuing.

### "Why hybrid retrieval and not just dense embeddings?"

> "Dense embeddings are great at paraphrases — 'how do I escalate an alert' will find the on-call playbook even if the doc says 'incident escalation procedure'. But they're weak on rare technical tokens — exact error codes, model names, regex patterns. BM25 is the opposite: precise on rare tokens, blind to paraphrases. I weighted them 0.6 dense / 0.4 sparse and tuned that split on my eval set — at 1.0/0.0 I lost 4 questions on rare-keyword queries, at 0.0/1.0 I lost 6 on paraphrased ones."

### "How do you know your RAG system is actually working?"

> "Three metrics, computed on every benchmark run. **Retrieval hit-rate** — does the right document appear in the top-K? That's the upper bound on what the generator can possibly get right. **Citation faithfulness** — does every cited doc actually exist in the retrieved set? That catches hallucinated citations. **Answer relevance** — embedding cosine between the predicted answer and the ground-truth answer. I deliberately didn't headline BLEU or ROUGE because they penalise paraphrase, which for QA is exactly the wrong thing to penalise."

### "What does your eval harness look like?"

> "It's a single Python script that loads 50 ground-truth question/answer pairs, runs each one through the pipeline, computes the three metrics plus latency, aggregates by difficulty, and writes JSON. The dashboard reads that JSON directly — single source of truth. I wanted the same numbers visible to me in CI and to a stakeholder on the dashboard."

### "What was the hardest part?"

Pick whichever resonates with your real experience:

- **Tuning the abstention threshold.** "Below 0.30 fused score we abstain rather than answer. Set it too high and you abstain on legitimate questions; set it too low and the LLM invents stuff. I ended up walking the curve manually because the eval set was small enough — in production this would need a proper validation set."
- **Keeping the brand tokenised.** "Every component has to resolve colour through Tailwind tokens — zero hardcoded hex anywhere. That discipline pays for itself the moment someone asks for a re-skin."
- **Deciding when to abstain.** Same idea, more philosophical: "A confidently wrong answer is worse than no answer in an enterprise QA setting. That's a product decision before it's a technical one."

### "What would you do next?"

> "Three things in order: (1) streaming responses, because LLM generation is most of the p95 latency and first-token-time is what users actually feel; (2) a query cache because internal QA traffic is heavily repeated; (3) a small calibration model on top of the retrieval scores, because my hand-tuned 0.30 threshold is fine for 50 questions but won't generalise."

### "How does this fit with the actual SMP stack?"

> "I'd love to learn what you use day-to-day. The shape of this project — typed gateway in front of a Python ML service — is deliberately stack-agnostic so it slots into most enterprise environments. If you're on a managed vector DB, the retriever swaps out cleanly; if you're behind SSO, the gateway is where that lives."

### "Tell me about a bug you hit."

If they ask, here's a real one to tell:

> "My lite benchmark was reporting 96% citation faithfulness instead of 100%. I assumed the metric was wrong. Turned out the extractive fallback was occasionally including a `[DOC-XXX]` marker from the chunk text in its output, even when that doc wasn't in the top-K — so the citation was 'real' to the answer but unfaithful to retrieval. I left the bug visible in the lite results because it's a useful demonstration of what citation faithfulness is actually catching."

### "What did you learn?"

> "How much eval discipline matters. My first iteration didn't have a benchmark and I had no way to tell whether my retrieval changes were helping. The day I sat down and built the 50-question suite, I caught two regressions I would have shipped otherwise. After that experience, no model goes anywhere without a baseline."

## STAR-format stories

### Story 1 — Built and evaluated a RAG pipeline (S/T/A/R)

- **Situation.** I wanted a portfolio piece that demonstrated production-style ML engineering, not a notebook.
- **Task.** Build an end-to-end document Q&A system with measurable quality.
- **Action.** Designed a three-service architecture, implemented hybrid retrieval (dense + BM25), built a 50-question ground-truth eval set, instrumented three RAG metrics (relevance, hit-rate, faithfulness), and surfaced everything on a dashboard.
- **Result.** 99.4% mean answer relevance, 100% retrieval hit-rate, 100% citation faithfulness on the production benchmark. p95 latency at 2.5s — flagged automatically as an SLO breach for follow-up. All findings reproducible from a single script.

### Story 2 — Made the system safe-by-default (S/T/A/R)

- **Situation.** RAG systems hallucinate. Confidently wrong answers in an enterprise context erode trust faster than no answer at all.
- **Task.** Build in safeguards before they were demanded.
- **Action.** Added a fused-score abstention gate (0.30), an append-only audit log capturing every query and its citations, a citation-faithfulness metric on every benchmark run, and a typed gateway with rate limiting and zod validation between the UI and the model.
- **Result.** The system can go from "demo" to "compliance review" without rewriting the core. Every guardrail has a concrete reference in the synthetic policy docs (DOC-003 PII, DOC-004 GenAI), modelling how I'd connect to real internal policies.

## Questions you should ask them

Pick two or three. The good ones are about the work itself, not perks.

1. "What does the rest of the AI/ML team's tooling look like — do you maintain a shared eval harness across models, or does each project bring its own?"
2. "How do you decide when an internal AI feature is ready to roll out to non-technical users?"
3. "What's the most painful part of moving a model from a notebook into production at SMP today?"
4. "Where does this internship fit into the team's roadmap — is there a specific shipping target you'd like the intern to contribute to?"
5. "Looking back at past interns, what separates the ones who got return offers from the ones who didn't?"

## Logistics

- Have the dashboard running on `localhost:3000` before the call. The standalone HTML demo (`SMP_DocuMind_Dashboard.html`) opens with no setup if their network blocks localhost.
- Have the README open in a tab; you'll point at the architecture diagram at least once.
- Have a fresh terminal ready in case they ask to see something. Don't share your editor window with personal stuff in it.
- Test screen sharing 30 minutes before. Always.

## Three things to keep in mind during the call

1. **They want to see how you think more than what you know.** When they ask a question you don't know the answer to, narrate the way you'd find out.
2. **Connect every answer back to what you built.** "I haven't used LlamaIndex specifically, but I built the equivalent retrieval layer myself in DocuMind, so I can speak to the trade-offs from first principles."
3. **Bring energy.** Internships are partly a bet on your trajectory. Be the candidate they'd actually want to sit next to for three months.

Good luck.
