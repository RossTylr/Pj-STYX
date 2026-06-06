# Virtual Wards — Hackathon Ideation, Evaluation & Synthesis

**Brief:** Challenge 3 (Virtual Wards) — clinician-facing dashboards, visual analytics, and automated analysis of remote-monitoring telemetry. Deliberately considerate of Challenge 2 (Hospital at Home) where the carer/family side connects.

**This document has three parts:**
1. **The corpus** — 512 distinct ideas across 40 thematic clusters (numbered continuously).
2. **The rubric** — a weighted scoring framework tuned for a *hackathon* (time-boxed, demo-driven, judged).
3. **The synthesis** — 16 buildable project concepts, each fusing a hero visual + a data-science core + a clinical hook, scored and ranked, with a single "if you build one thing" recommendation.

The challenge text essentially describes one project — *patient recovery as a trajectory through a multi-dimensional state space, with GNNs mapping the physiological interactions*. The corpus surrounds that core with everything adjacent, so the synthesis can pick the strongest spine and the best showpieces to hang on it.

---

## PART 1 — THE CORPUS (512 ideas)

### A. State-space & trajectory visualisation (the core Challenge-3 idea)
1. Project each patient's full vital-sign vector into a 2-D latent space (VAE/UMAP) and render their stay as a path, current position a pulsing marker.
2. Learn "stability basins" and "crisis attractors" from historical cohorts and shade the map so a clinician instantly sees which region the patient is drifting toward.
3. Velocity encoding: marker tail length ∝ rate-of-change, so fast deteriorators literally streak across the map.
4. Acceleration glyph: a small arrow showing not just heading but whether the trend is speeding up or slowing.
5. Phase-portrait view plotting two coupled signals (e.g. HR vs SpO2) with a fading time-trail to reveal limit cycles vs spirals into instability.
6. Time-as-altitude 3-D ribbon: the 2-D path extruded over time so the whole stay is one readable sculpture.
7. Return map (each measurement vs the previous) to expose loss of physiological variability — a flattening return map is an early warning.
8. Per-patient recurrence plot: repeating states render as texture; texture breakdown signals regime change.
9. Colour the trajectory by learned geodesic distance-to-discharge (proximity to the typical "ready to leave" region).
10. Mirror of #9: colour by proximity to the nearest historical crisis trajectory.
11. Trajectory "tube" whose radius is prediction uncertainty — thick where sensors are unreliable, thin where data is dense.
12. Overlay the cohort's "healthy recovery corridor" as a translucent channel; flag exit from the corridor.
13. Counterfactual ghost trail: a faint projected path of where the patient would be on yesterday's trend, beside the actual path.
14. Multi-resolution zoom from whole-stay overview smoothly into the last hour at full sensor resolution.
15. Brushing-and-linking: select a trajectory segment and have raw waveform panels highlight the exact window that produced it.
16. Attractor-switching waypoint: annotate the moment dynamics jump from one basin to another.
17. Trajectory "echo": surface the three most similar historical patients' paths as faint overlays, outcomes labelled.
18. Latent-space "fingerprint" thumbnail — a tiny state-path sparkline usable as the patient's avatar everywhere in the UI.

### B. Cohort / ward-level views
19. Ward-as-constellation: every patient a glyph in shared latent space; the whole ward legible in one picture.
20. Sort the roster by "time-to-likely-escalation," newest crises bubbling to the top.
21. Small-multiples grid of every patient's trajectory thumbnail so triage is one eye-sweep.
22. Motion-priority animation of the last 6 h: patients moving toward red catch the eye by motion alone.
23. Heat-strip roster — one row per patient, a horizontal band coloured by risk over time (a Gantt of stability).
24. Bubble-up alarms that nudge a glyph upward and brighten it in proportion to deterioration *slope*, not absolute value.
25. Auto-discover "patient archetypes" nightly and group the roster by archetype.
26. Caseload balancer showing which clinician carries the most cumulative *predicted risk*, not just headcount.
27. "Quietest patient" flag surfacing stable patients safe to deprioritise.
28. Ward entanglement map — a network linking patients with correlated deterioration (shared infection/environmental signal).
29. Sparkline wall: a dense Minard-style wall of every vital for every patient, scannable in seconds.
30. Discharge-readiness leaderboard ranking who can leave the ward soonest to free capacity.
31. Newly-admitted spotlight auto-highlighting patients with too little history for confident prediction.
32. Two-up compare: drag any two patients side-by-side to see trajectories and divergence point.
33. Ward "tide chart" aggregating stability across all patients into one rising/falling line for handover.

### C. Deterioration & risk encoding
34. Risk as a horizon "waterline" — each patient's stability probability is a level; rising = improving, sinking = deteriorating.
35. Dual-channel colour: hue = current risk, saturation = confidence (a pale-red patient reads as "maybe high risk, but unsure").
36. Slope badges (↗ ↘ →) on every metric so the trend is legible without reading numbers.
37. "Reserve" gauge visualising physiological reserve (how much shock the patient can still absorb), not current vitals alone.
38. Deterioration "fuse" — a burning-fuse bar whose remaining length is predicted time-to-escalation.
39. Ban the traffic light: use a continuous deterioration gradient to avoid threshold cliff-edges.
40. Compound-risk ring — a radial chart where each arc is one organ-system's contribution to total risk.
41. "Distance from your own normal" meter rather than distance from population thresholds.
42. Risk-momentum quadrant: current risk (x) vs rate of change (y); top-right = high and worsening.
43. Shade the background of each numeric panel by that variable's contribution to overall risk right now.
44. Catastrophe-surface visual rendering the cusp where small changes could trigger sudden collapse.
45. Stability "battery" icon draining as reserve is consumed, recharging on recovery.
46. Encode variability loss explicitly — narrowing HRV band, a known deterioration sign.
47. "Silent deterioration" flag for patients whose absolute numbers look fine but whose trend is adverse.

### D. Temporal & longitudinal displays
48. Horizon graphs for every vital, stacked densely so 12 signals fit where one line chart usually sits.
49. Stream-graph of the patient's "state mixture" over time (proportion stable / watch / critical).
50. Timeline with auto-annotated clinical events (meds, interventions, alarms) aligned to vital traces.
51. Calendar multi-day view for longer stays, each day a sparkline cell.
52. "Day vs night" folded view to expose nocturnal deterioration easily missed.
53. Elastic time axis compressing stable stretches and expanding volatile ones automatically.
54. Sliding-window replay scrubber to re-watch the last deterioration like game footage.
55. Auto-placed change-point markers wherever the model detects a regime shift.
56. "Since last review" shading so a clinician sees exactly what changed while they were away.
57. Trend-decomposition panel splitting each signal into baseline + cycle + residual.
58. "What's new" digest auto-generated per patient for the last N hours at handover.
59. Forecast-vs-actual ribbon showing where reality diverged from yesterday's prediction (model trust over time).
60. Multi-scale time bricks — a row of hour-bricks coloured by stability, drillable to the minute.
61. Event-locked averaging: align all past alarms to t=0 to reveal this patient's typical pre-alarm signature.

### E. High-density / Minard-style composites
62. A single Minard-style "patient stay" poster: flow width = stability, colour = risk, annotations = interventions, one canvas.
63. Whole-ward Minard map: flows per patient converging toward "discharge" or diverging toward "escalation."
64. Sankey of ward state transitions across the shift (stable→watch→critical→back).
65. Layered band chart stacking all organ systems on a shared time axis with one risk ribbon on top.
66. "Flight recorder" strip — the densest possible one-line stay summary, designed for print handover.
67. Dense board fitting an entire 30-bed ward on one screen via glyph miniaturisation.
68. "Vitals tartan" — a woven texture where each thread is a normalised signal; pattern disruption = problem.
69. Minard-inspired discharge report combining trajectory, interventions and outcome in one shareable image.
70. High-density anomaly mosaic — a grid of (patient × hour) anomaly scores.
71. Information-dense hover tooltip rendering a complete mini-history without leaving the overview.
72. Single-glance shift-summary infographic auto-built at the end of every shift.
73. Layered small-multiples each encoding 8+ variables yet staying scannable.
74. Print-first dense report for wards with poor connectivity or fallback workflows.

### F. Alerting, triage & attention management
75. Predictive alerts firing on the *forecast* crossing a threshold in N hours, not the threshold being crossed now.
76. Alarm-fatigue throttle suppressing redundant alerts via a learned model of which alarms clinicians act on.
77. "Why this alert" one-liner on every notification, naming the top driving signal.
78. Tiered escalation (nudge → notify → page) with tier set by predicted severity and time-to-crisis.
79. Attention-budget view allocating a finite "attention score" across the ward to show where to spend it.
80. Snooze-with-conditions: defer an alert; it re-fires only if the trend worsens.
81. Cross-patient correlated-alarm grouping so a cluster of related alerts becomes one actionable card.
82. Silent-but-rising watchlist separate from active alarms, for slow adverse trends.
83. Confidence-gated alerts that hold back when data quality is too poor, flagging "check sensor" instead.
84. Alert provenance trail: tap an alarm to see the exact data window and model output that triggered it.
85. Role-aware routing sending each alert to nurse vs doctor based on predicted action needed.
86. De-escalation notices actively telling clinicians a patient has stabilised.
87. Replay-and-learn loop where dismissed alerts retrain the suppression model.
88. Shift-aware alerting batching non-urgent items for handover rather than interrupting.

### G. Comparison & benchmarking
89. Patient-vs-self: overlay today's trajectory on the same patient's path from 48 h ago.
90. Patient-vs-cohort: show where this patient sits in the distribution of similar admissions.
91. Patient-vs-twin: surface the single most similar past patient and their outcome as an anchor.
92. Expected-vs-observed corridor per vital given diagnosis and time-since-admission.
93. Recovery-pace percentile ("recovering faster than 70% of similar cases").
94. Benchmark against the patient's pre-admission baseline pulled from prior records if available.
95. Cross-ward benchmarking of outcomes to find which monitoring protocols correlate with better recovery.
96. "Sibling cohort" view grouping patients admitted for the same condition this week.
97. Divergence alert when a patient drops below their matched cohort's recovery corridor.
98. Outcome-conditioned overlays: show separately the paths of similar patients who recovered vs deteriorated.
99. Personal-record markers (best HRV, lowest resting HR this stay) to motivate a recovery framing.
100. Cohort-drift monitor detecting when the ward population differs from the model's training distribution.

### H. Uncertainty & confidence
101. Prediction cones rendering the forecast as a widening cone of plausible futures, not a single line.
102. Hurricane-track metaphor for deterioration: a most-likely path plus a probability envelope.
103. Confidence-coloured everything — every model output carries a visible confidence channel.
104. Calibration ribbon shown to clinicians so they learn when to trust the model.
105. "Model is unsure" honest-state UI that says so rather than fabricating false precision.
106. Ensemble-disagreement fan showing the spread across multiple models.
107. Data-sufficiency meter per prediction (how much history backs the estimate).
108. Quantile bands (10/50/90) for each forecasted vital.
109. Time-decay of confidence — forecasts visibly fade further into the future.
110. Out-of-distribution warning when the patient's state is unlike anything in training.
111. Counterfactual robustness: how stable the escalate/observe recommendation is to small data changes.
112. Conformal-prediction intervals giving statistically guaranteed coverage on each forecast.
113. "Two experts disagree" flag when a clinical-rule score and the ML model conflict, surfacing both.

### I. Data quality, missingness & sensor health
114. Sensor-health strip showing per-device signal quality beside the vitals it feeds.
115. Missingness ribbon making data gaps explicit rather than silently interpolating.
116. Distinguish "stable and quiet" from "no data" — never let absence read as normality.
117. Artefact detector flagging motion/contact artefacts and greying out affected segments.
118. Battery-and-connectivity tile per device (a dead sensor is a clinical risk).
119. Imputation-honesty shading so clinicians see measured vs inferred values.
120. Adaptive trust automatically down-weighting predictions when input quality drops.
121. Prominent "last reliable reading" timestamp on every vital.
122. Sensor-drift detector comparing a device's readings to expected ranges over time.
123. Cross-sensor consistency check (chest-strap HR vs PPG HR) flagging disagreement.
124. Data-completeness score feeding how much screen prominence a patient gets.
125. Auto "please re-site sensor" carer prompt when quality degrades (Challenge-2 bridge).
126. Graceful degradation to simpler robust indicators when rich data is missing.

### J. Explainability & interpretability
127. SHAP-style contribution bars showing which signals drove each risk score right now.
128. Natural-language rationale auto-written per prediction ("rising RR and falling SpO2 over 3 h").
129. Attention-weight overlay (transformer models) highlighting which time windows the model focused on.
130. Counterfactual explanation ("if RR were 4 lower, risk would drop from high to moderate").
131. Example-based explanation surfacing the nearest historical cases behind a prediction.
132. Feature-interaction map showing which signal *pairs* jointly drive risk, not just individually.
133. Transparent fallback to an interpretable rule model when the deep model can't explain itself.
134. "What changed the score" diff between this hour's and last hour's risk drivers.
135. Saliency on the trajectory itself, highlighting which segment most influenced the estimate.
136. Clinician-editable model: mark a false alarm and watch the model's reasoning update.
137. Confidence-and-cause card pairing the risk, its confidence, and its top three causes.
138. Glossary-linked outputs so any model term is one tap from a plain explanation.
139. Full audit log of every model decision for retrospective review and governance.

### K. Glanceable / mobile / ambient
140. Smartwatch glance for on-call clinicians — one colour and one number per assigned patient.
141. Ambient ward wall-display showing the constellation for passive monitoring.
142. Lock-screen widget summarising the highest-risk patient and trend.
143. Haptic escalation on a paired device, intensity scaled to urgency.
144. Ward sonification — rising risk subtly raises a tone, monitorable without looking.
145. Single-thumb mobile triage list for a clinician walking between rooms.
146. Notification-as-summary — each push a complete mini-briefing, not just "check patient X."
147. Offline-first mobile cache so the last known state is always available on poor networks.
148. Colour-blind-safe palette as the default across all glanceable surfaces.
149. "At-a-glance handover" mode collapsing everything to a single shift-summary card.
150. Tablet bedside mode for in-person rounds mirroring the remote view.
151. Voice query ("how's bed 7 trending?") returning a spoken one-line status.

### L. 3-D / immersive / spatial
152. 3-D latent-space fly-through letting the clinician orbit the patient's trajectory.
153. VR ward where each patient is a star and you walk among them, distance encoding risk.
154. Stereoscopic phase-space for genuinely 3-coupled signals (HR, RR, SpO2).
155. AR bedside overlay projecting the trajectory above the patient on rounds.
156. Spatial-audio cueing in VR so deteriorating patients are "heard" from their direction.
157. Volumetric density cloud of where the patient's state has spent the most time.
158. Tabletop holographic ward for multidisciplinary team meetings.
159. Gesture navigation to grab and inspect any trajectory in 3-D.
160. "Terrain" metaphor rendering the risk landscape as topography, the patient a ball rolling on it.
161. Depth = time, so the scene literally has the past behind and the forecast ahead.
162. Multi-patient 3-D braid showing entangled deterioration across a small cohort.
163. Lightweight WebXR demo running in-browser for a judge with no headset setup.

### M. Interaction & clinician workflow
164. One-click "I've reviewed this" acknowledgement that timestamps and quiets the patient appropriately.
165. Annotation layer to pin notes to a trajectory point for colleagues.
166. Handover-builder that auto-drafts the shift summary for the clinician to edit before sending.
167. Customisable triage rules per clinician, learned and suggested over time.
168. "Focus mode" hiding stable patients to cut cognitive load on a busy shift.
169. Undo/redo on any view configuration so exploration is safe.
170. Saved layouts per condition (a "post-op" layout vs a "respiratory" layout).
171. Inline action from an alert (call patient, request manual obs) without leaving the view.
172. Collaborative cursors so two clinicians review the same patient remotely together.
173. Role-aware UI surfacing different detail to nurses, doctors and consultants.
174. Keyboard-driven power-user mode for rapid ward sweeps.
175. "Explain to me" button walking a junior clinician through the reasoning step by step.
176. Workflow-timing analytics showing where clinician attention is bottlenecked.

### N. Graph Neural Network methods
177. Model each patient as a graph of physiological subsystems; a GNN learns inter-system coupling to predict deterioration.
178. Spatio-temporal GNN over a sensor graph (nodes = sensors, edges = learned correlations evolving in time).
179. Dynamic graph learning that *infers* the time-varying dependency structure between vitals rather than assuming it.
180. Patient-similarity graph across the ward; a GNN propagates risk signals between similar patients.
181. Heterogeneous graph combining vitals, labs, meds and demographics as typed nodes.
182. Graph attention to expose which physiological edge (e.g. cardio-respiratory coupling) most drives risk — interpretable by design.
183. Temporal message-passing where each node carries a recurrent state, fusing GNN + RNN.
184. Granger-causal graph estimation feeding a GNN so edges carry a causal reading.
185. Multi-patient graph for detecting shared exogenous events (environmental/infectious signal across beds).
186. Graph-level readout predicting a single ward-stability score from the subsystem graph.
187. Edge-prediction task forecasting emerging abnormal couplings before single signals move.
188. Hierarchical GNN (sensor → subsystem → patient → ward) rolling information up the hierarchy.
189. Graph contrastive pretraining on unlabelled telemetry to learn physiological structure cheaply.
190. Physiology-informed graph priors (known anatomical couplings) to regularise the GNN with little data.
191. Explainable GNN via minimal-subgraph extraction — the smallest subgraph explaining a high-risk prediction.
192. Lightweight few-layer GraphSAGE sized to run in real time on streaming telemetry for the hackathon.

### O. Trajectory clustering & phenotyping
193. Cluster patient trajectories to discover recovery phenotypes (fast, slow, relapsing).
194. Dynamic-time-warping distance for shape-aware trajectory clustering.
195. Latent-trajectory mixture model assigning each patient a probability over recovery archetypes.
196. Online phenotype assignment updating as new data arrives.
197. Trajectory motifs — mine recurring short patterns (e.g. a pre-crisis signature) across patients.
198. Soft clustering so a patient can be 60% "stable recovery," 40% "at-risk."
199. Phenotype-conditioned forecasting using the model specialised to that archetype.
200. Visualise the cluster landscape so clinicians see the patient's "type" and its typical outcome.
201. Treat phenotype switching as an early-warning event in itself.
202. Sub-phenotype discovery within a diagnosis to personalise monitoring thresholds.
203. Transfer phenotypes learned in hospital monitoring to the virtual-ward setting.
204. Trajectory autoencoder producing a compact embedding for clustering and retrieval.
205. Rare-phenotype flag for patients fitting no known cluster, prompting human review.

### P. Deterioration prediction models
206. Sequence model (LSTM/GRU/Temporal-CNN) forecasting next-N-hours vitals and deterioration probability.
207. Transformer with time-aware positional encoding for irregularly sampled telemetry.
208. Multi-horizon prediction (1 h / 4 h / 12 h) from one model with horizon-specific heads.
209. Multi-task model jointly predicting deterioration, length-of-stay and readmission risk.
210. Hazard model outputting instantaneous risk, interpretable as "danger right now."
211. Hybrid: clinical early-warning score as a feature into the ML model for a safe performance floor.
212. Self-correcting forecaster comparing prior predictions to outcomes and recalibrating online.
213. Mixture-density network outputting full predictive distributions per vital.
214. Neural ODE modelling continuous physiological dynamics between irregular samples.
215. Early-warning tuned for high recall on rare crises, with the precision trade-off made visible.
216. Personalised fine-tuning adapting a population model to each patient as data accrues.
217. Lead-time optimisation — train explicitly to maximise warning time before an event.
218. Two-stage compute: cheap screen on all patients, expensive deep model only on flagged ones.
219. Robust model trained with missingness and noise augmentation to survive real data.

### Q. Survival & time-to-event
220. Time-to-deterioration as a survival problem with right-censoring for patients who recover/discharge.
221. Cox proportional-hazards baseline on engineered telemetry features (familiar, interpretable).
222. DeepSurv / neural survival model capturing non-linear feature effects.
223. Competing-risks model separating "deteriorate," "discharge" and "transfer."
224. Dynamic survival prediction updated continuously as telemetry streams in.
225. Time-varying-covariate Cox so the hazard responds to the latest vitals.
226. Per-patient survival curve: probability of remaining stable over the next 24 h.
227. Restricted-mean-stable-time as a single summary metric for the shift glance.
228. Landmark survival models re-anchored at each review to avoid immortal-time bias.
229. Calibrated survival outputs validated with time-dependent concordance for the demo.
230. Personalised "stability half-life" estimate communicated simply.
231. Survival-based discharge timing — predict when stability probability is high enough to leave the ward.
232. Joint longitudinal-survival model linking the vital trajectory to the hazard explicitly.

### R. Anomaly & novelty detection
233. Autoencoder reconstruction error as a per-patient anomaly score over time.
234. Personalised one-class model learning each patient's own normal and flagging departures.
235. Multivariate anomaly detection catching abnormal *combinations* even when each signal is in range.
236. Change-point detection on the multivariate stream to catch regime shifts early.
237. Spectral-residual or matrix-profile methods for fast streaming anomaly scoring.
238. Contextual anomalies (abnormal-for-this-time-of-day or this-stage-of-recovery).
239. Collective-anomaly detection across the ward (several patients odd at once → systemic cause).
240. Novelty detection for states never seen in training, flagged for human attention.
241. Anomaly explanation pointing to the specific signal/segment responsible.
242. Threshold-free anomaly ranking so clinicians triage by relative oddness.
243. Self-supervised anomaly pretraining on abundant unlabelled telemetry.
244. Drift-aware anomaly model recalibrating "normal" as the patient recovers.

### S. Multivariate time-series methods
245. Multivariate state-space (Kalman/particle) filtering to denoise and forecast vitals jointly.
246. Vector autoregression for short-term inter-signal dynamics with interpretable coefficients.
247. Dynamic factor model extracting a few latent physiological drivers from many sensors.
248. Cross-correlation / coherence analysis between signal pairs to detect decoupling.
249. Wavelet decomposition to monitor signals across multiple frequency bands at once.
250. Hidden-Markov / switching state-space model with labelled regimes (stable/watch/critical).
251. Gaussian-process regression for smooth, uncertainty-aware interpolation of irregular samples.
252. Multi-output GP sharing information across correlated vitals.
253. Tensor decomposition over (patient × signal × time) to find ward-wide patterns.
254. Functional data analysis treating each vital as a smooth curve for shape features.
255. Lagged-feature library capturing rates, accelerations and rolling statistics for downstream models.
256. Symbolic aggregate approximation (SAX) discretising streams for fast pattern matching.
257. Spectral entropy as a compact cross-signal instability indicator.

### T. Latent / state-space inference
258. Variational autoencoder mapping high-dimensional vitals to a low-dimensional health state.
259. Sequential VAE (deep Markov model) giving a temporally coherent latent trajectory.
260. Disentangled latent space whose axes align to interpretable physiology (perfusion, oxygenation).
261. Latent-ODE for continuous-time state evolution between irregular observations.
262. Switching linear dynamical system capturing distinct physiological modes.
263. Contrastive predictive coding learning a state representation that forecasts the near future.
264. Latent distance-to-discharge and distance-to-crisis as headline scalars.
265. Probabilistic latent state with uncertainty propagated into the trajectory-tube width.
266. Cross-patient shared latent space enabling cohort comparison in a common frame.
267. Latent-space arithmetic simulating "what if this intervention shifts the state here."
268. Slow-feature analysis extracting the slowly-varying components that track true recovery.
269. Self-supervised masked-reconstruction pretraining of the state encoder.
270. Online filtering of the latent state for a real-time, smooth trajectory display.

### U. Causal & counterfactual
271. Counterfactual forecasting: trajectory under "no intervention" vs "intervene now."
272. Treatment-effect estimation for monitoring/escalation decisions from observational ward data.
273. Causal-discovery on telemetry to propose (with caveats) directional physiological links.
274. "What if we increased monitoring frequency" simulation.
275. Counterfactual alert explanations (the minimal change that would have averted the warning).
276. Attribution partition splitting outcome drivers into patient-state vs system-action vs noise.
277. Synthetic-control comparison for evaluating a protocol change across the ward.
278. Time-varying confounding adjustment (g-methods) for honest effect estimates.
279. Causal-graph viewer letting clinicians inspect and edit assumed relationships.
280. Intervention ranking by predicted causal benefit per patient.
281. Mediation analysis showing through which signal an intervention is likely to act.
282. Sensitivity analysis quantifying robustness of a causal claim to unmeasured confounding.

### V. Signal processing & feature extraction
283. Heart-rate-variability suite (time, frequency, non-linear) as deterioration markers.
284. Respiratory-rate stability and apnoea-pattern features from the breathing signal.
285. SpO2 desaturation-event detection (depth, duration, frequency).
286. Pulse-transit-time as a blood-pressure-trend surrogate from multi-sensor timing.
287. Actigraphy/mobility features as a recovery proxy (more movement = recovering).
288. Sleep-quality estimation from overnight signals as a recovery indicator.
289. PPG morphology features beyond heart rate.
290. Per-window signal-quality indices gating downstream models.
291. Circadian-rhythm features detecting loss of normal day-night variation.
292. Cross-signal timing features (HR-RR phase relationship).
293. Energy-expenditure estimation from accelerometry for recovery tracking.
294. Cough/sound-event detection from a bedside microphone (with consent) as a respiratory marker.

### W. Multimodal fusion
295. Fuse continuous vitals with intermittent manual obs into one coherent state estimate.
296. Combine telemetry with medication/intervention timelines for context-aware prediction.
297. Integrate patient-reported symptoms (from the Challenge-2 app) as an extra modality.
298. Fuse imaging or lab results when available as sparse but high-value nodes.
299. Incorporate nursing notes via a language model into the risk estimate.
300. Wearable + environmental data fusion (room temperature, humidity) for context.
301. Late-fusion ensemble combining per-modality specialists with learned weighting.
302. Early-fusion transformer ingesting heterogeneous, irregularly-timed events.
303. Cross-modal attention so the model learns which modality matters when.
304. Missing-modality robustness so the system degrades gracefully when a stream drops.
305. Carer-reported observations (appetite, mood, mobility) folded in as soft signals (Challenge-2 bridge).

### X. Topological data analysis
306. Persistent homology on the trajectory point-cloud to quantify physiological loops and stability.
307. Mapper graph of the cohort's state space to reveal branch points between recovery and decline.
308. Topological features (Betti numbers, persistence stats) as inputs to the deterioration model.
309. Detect loss of a stable cycle (a topological signature) as an early-warning marker.
310. Sliding-window embedding + persistence to track topology change over time.
311. Mapper-based cohort map as a navigable clinician view.
312. Persistence-landscape features for robust, vectorised trajectory description.
313. Topological anomaly detection flagging states with unusual local structure.
314. Compare a patient's topological signature to recovered-vs-deteriorated reference signatures.
315. A giotto-tda pipeline for the demo implementation.
316. Bottleneck-distance similarity between patients' state topologies.

### Y. Foundation / transfer / self-supervised
317. Pretrain a physiological time-series foundation model on large public data, fine-tune on virtual-ward data.
318. Self-supervised masked-vital modelling to learn representations without labels.
319. Transfer a hospital-monitoring model to the home setting with domain adaptation.
320. Few-shot adaptation to new conditions with limited virtual-ward examples.
321. Use a pretrained time-series transformer as a forecasting backbone.
322. Contrastive pretraining pairing augmented views of the same patient window.
323. Domain-adversarial training to bridge hospital-vs-home distribution shift.
324. Continual learning so the deployed model keeps improving without forgetting.
325. Representation reuse across tasks (deterioration, phenotyping, anomaly) from one shared encoder.
326. Public-dataset bootstrapping (MIMIC-style ICU data) to cold-start the model.
327. Knowledge distillation from a large model into a tiny edge-deployable one.
328. Prompt a clinical LLM to summarise telemetry trends into narrative handover text.

### Z. Decision support & policy (RL / POMDP)
329. Frame monitoring/escalation as a POMDP and learn a policy recommending observe/escalate/discharge.
330. Off-policy evaluation of escalation policies on historical data before any deployment.
331. Expected-value-of-information — tell clinicians which extra measurement would most reduce uncertainty.
332. Optimal monitoring-frequency policy balancing safety against patient burden and cost.
333. Risk-sensitive RL deliberately conservative near crisis states.
334. Constrained policy that can never violate hard clinical safety rules.
335. Recommend-and-explain — every policy suggestion carries its expected outcome and confidence.
336. Discharge-timing optimisation trading ward capacity against readmission risk.
337. Active-sensing policy requesting a manual obs only when it will change the decision.
338. Bandit approach learning which alert types each clinician finds actionable.
339. Counterfactual policy comparison ("current protocol vs proposed") on synthetic patients.
340. Human-override-aware policy learning from disagreement.
341. Decision-curve analysis showing net clinical benefit across thresholds.

### AA. Privacy, federation & security
342. Federated learning across multiple virtual wards without moving patient data.
343. Differential privacy on training to protect individuals.
344. On-device inference so raw telemetry never leaves the home.
345. Synthetic-data sharing for collaboration in place of real records.
346. Secure aggregation for federated model updates.
347. Role-based access control with full audit trails for governance.
348. De-identification pipeline for any data used in the demo.
349. Privacy-preserving patient-similarity search without exposing raw records.
350. Consent-aware data flows where patients/carers control what is shared.
351. Tamper-evident logging of model decisions for medico-legal defensibility.
352. Edge-cloud split transmitting only abstracted state, not raw signals.

### AB. Synthetic data & simulation
353. Build a virtual-ward patient simulator generating realistic telemetry for the hackathon.
354. Inject scripted deterioration events to demo early-warning lead time.
355. Copula-based synthetic vitals preserving inter-signal correlations.
356. Physiology-informed generator (simple compartmental models) for plausible dynamics.
357. Scenario library (sepsis onset, respiratory decline, cardiac event) for repeatable demos.
358. Adjustable-difficulty cases to stress-test the model live for judges.
359. Synthetic missingness and sensor failure to demonstrate robustness.
360. Digital-twin patient whose simulated trajectory the dashboard tracks in real time.
361. Augmentation engine expanding scarce real data for training.
362. Counterfactual-scenario generator ("what if we'd intervened 2 h earlier").
363. Generative model (GAN/diffusion) for realistic multivariate vital sequences.
364. Replay engine streaming a synthetic patient through the live pipeline for the demo.

### AC. Human-in-the-loop & active learning
365. Clinician feedback loop where confirmed/false alarms retrain the model.
366. Active learning querying clinicians on the most informative ambiguous cases.
367. Label-efficient pipeline using clinician acknowledgements as weak labels.
368. Interactive threshold tuning showing live sensitivity/specificity trade-offs.
369. Disagreement capture logging clinician overrides to improve the model.
370. Trust-calibration training mode showing clinicians model hits and misses.
371. "Teach the model" interface for flagging spurious features.
372. Preference learning over alert styles to personalise notifications.
373. Crowd-of-clinicians consensus labels for ambiguous deterioration events.
374. Continual-feedback dashboard showing how clinician input improves performance.
375. Safe exploration running new suggestions in shadow mode before going live.

### AD. Personalised baselines & normalisation
376. Learn each patient's personal "normal" in the first hours and judge deviation against it.
377. Demographic-adjusted baselines (age, comorbidity) for fairer thresholds.
378. Circadian-aware baselines so night-time values aren't misread.
379. Activity-adjusted vitals (HR after movement vs at rest) using accelerometry context.
380. Medication-aware baselines accounting for drug effects on vitals.
381. Adaptive baselines shifting as the patient genuinely recovers.
382. Per-patient variability bands rather than fixed population ranges.
383. Baseline-confidence weighting when history is short.
384. Pre-admission baseline import when prior records exist.
385. Personal-percentile display ("high for you, normal for the population").
386. Recovery-trajectory-relative normalisation (expected value given days-since-admission).

### AE. Clinical scores & escalation logic
387. Continuous NEWS2 computed from streaming telemetry rather than intermittent spot checks.
388. ML-augmented early-warning score blending NEWS2 with learned features for higher lead time.
389. Soft-NEWS2 avoiding hard threshold cliff-edges with a smooth risk surface.
390. Condition-specific scores (respiratory vs cardiac virtual wards).
391. Escalation pathway encoded as explicit, auditable rules layered over the ML.
392. Score-vs-model agreement indicator surfacing both for clinician judgement.
393. Trend-aware scoring weighting the trajectory, not just the latest value.
394. Personalised escalation thresholds tuned per patient with clinical sign-off.
395. Sepsis-screening bundle integrated with continuous monitoring.
396. Time-in-deteriorating-range as an accumulating risk metric.
397. Automatic escalation-bundle prompts (which checks/actions to run) on threshold crossing.
398. Score provenance making every contributing measurement inspectable.

### AF. Capacity, logistics & system optimisation
399. Ward-capacity forecasting from aggregate discharge-readiness predictions.
400. Optimal patient-to-clinician assignment balancing predicted workload.
401. Predict which patients can be safely stepped down to free monitoring capacity.
402. Surge-planning view forecasting demand on the virtual ward.
403. Equipment/sensor inventory tracking tied to admissions.
404. Visit-routing optimisation for any required in-person home visits.
405. Cost-aware monitoring intensity (more sensors for higher-risk patients).
406. Bottleneck analytics showing where clinician response is delayed.
407. Admission-suitability screen predicting who is a good virtual-ward candidate.
408. Readmission-risk forecast informing discharge from the virtual ward itself.
409. Resource-allocation simulation under different staffing levels.
410. SLA monitoring on alert response times with breach prediction.

### AG. Bridges to Challenge 2 (carers & families)
411. Two-sided system: a clinician dashboard and a carer app sharing one underlying patient-state model.
412. Plain-language translation of the clinician risk state into "what this means for you today."
413. "What to watch for" card generated from the patient's specific risk drivers.
414. Threshold-aware carer guidance ("if you see X, call us") tuned to this patient's risks.
415. Carer-reported observations (mood, appetite, mobility) flowing back as soft model inputs.
416. Shared situational awareness — carer and clinician see a consistent picture at different detail levels.
417. Confidence-appropriate messaging that never over-alarms the family when the model is unsure.
418. Carer-prompted sensor fixes ("please re-site the chest strap") to maintain data quality.
419. One-tap "request a call" from the carer arriving context-rich on the clinician side.
420. Reassurance signalling — actively tell the family when things are stable to reduce anxiety.
421. Medication and care-task reminders for the carer linked to the clinical plan.
422. Escalation hand-off where a carer concern is elevated with full telemetry context.
423. Just-in-time education micro-content surfaced from the patient's current state.
424. Family-friendly trajectory view — a simplified, non-alarming version of the clinician trajectory.

### AH. Communication & notification orchestration
425. Smart routing of each alert to the right person at the right time across the care team.
426. Notification de-duplication so carer and multiple clinicians aren't separately spammed.
427. Escalation ladder with timeouts (no acknowledgement in X minutes → escalate).
428. Context-rich messages bundling the trajectory snapshot with every notification.
429. Two-way secure messaging between carer and clinical team in-app.
430. Quiet-hours logic batching non-urgent items respectfully.
431. Read-receipts and acknowledgement tracking for accountability.
432. Multi-channel delivery (push, SMS fallback, call) by urgency.
433. Pre-drafted message templates for common clinician responses.
434. Closed-loop confirmation that an action was taken after an alert.
435. Handover packaging bundling overnight events for the morning team.
436. Language-localisation of carer notifications for non-English-speaking families.

### AI. Architecture, streaming & edge
437. Real-time streaming pipeline (Kafka-style) ingesting continuous telemetry.
438. Edge pre-processing on a home hub to compute features and cut bandwidth.
439. Incremental/online model updates rather than batch retraining.
440. Backpressure-tolerant ingestion surviving intermittent home connectivity.
441. Time-series database optimised for high-frequency multivariate vitals.
442. Event-driven architecture where predictions trigger downstream notifications.
443. Low-latency inference service meeting clinical response-time needs.
444. Replay/backfill capability to reprocess history when models improve.
445. Lightweight in-browser inference (ONNX/WASM) for a serverless hackathon demo.
446. Stream-windowing strategy (tumbling vs sliding) tuned to clinical relevance.
447. Graceful offline mode caching state on the home device.
448. Horizontal scalability to thousands of concurrent virtual-ward patients.

### AJ. Interoperability & standards
449. FHIR-conformant data model so it plugs into NHS/hospital records.
450. HL7 messaging for integration with existing clinical systems.
451. SNOMED-CT coding of events and observations.
452. Open device-data standards (IEEE 11073) for sensor integration.
453. openEHR archetypes for portable clinical content.
454. dm+d-coded medications for safe interoperability.
455. Standard alert formats so notifications integrate with existing paging.
456. API-first design so dashboard and carer app share one backend.
457. Vendor-neutral sensor adapters to avoid lock-in.
458. NHS-login / identity integration for secure access.

### AK. Evaluation, validation & trust
459. Prospective silent-mode evaluation comparing model alerts to actual events before go-live.
460. Lead-time-to-event as the headline clinical metric, not just AUC.
461. Alarm-burden metric (alerts per patient-day) to demonstrate fatigue reduction.
462. Calibration assessment so probabilities mean what they say.
463. Decision-curve / net-benefit analysis for clinical usefulness.
464. Subgroup fairness audit across age, sex, ethnicity, comorbidity.
465. Failure-case gallery documenting where the model breaks.
466. Ablation study isolating each component's contribution.
467. Robustness testing under injected noise and missingness.
468. Clinician trust survey as a qualitative outcome.
469. Reproducibility with fixed seeds and logged experiments.
470. Regulatory-readiness mapping to medical-device-software expectations.

### AL. Demo, narrative & hackathon delivery
471. Anchor the demo on one synthetic patient whose live deterioration the system catches early — a clear story arc.
472. Three-scene pitch: stable patient, silent deterioration caught, crisis averted.
473. Side-by-side "standard dashboard vs our trajectory view" to show instant legibility gains.
474. Live "speed-up time" control so judges watch hours of recovery in seconds.
475. A single hero visual (the trajectory map) as the memorable centrepiece.
476. Pre-baked synthetic data so the demo never depends on a live feed.
477. A clear MVP boundary: one ward, one condition, one prediction, one killer view.
478. A quantified "lead time gained" headline number for the pitch.
479. Clinician-quote framing of the problem (alarm fatigue, dashboard overwhelm) to open.
480. A fallback recorded demo video in case of live failure.
481. A crisp one-page architecture diagram for the technical judges.
482. A "what we'd do next" slide bridging to Challenge 2 and to validation.
483. A memorable codename and brand for the project.

### AM. Wildcards & moonshots
484. Digital twin per patient simulating "what if" interventions in real time.
485. Generative "patient avatar" that visibly looks unwell as risk rises (intuitive, non-numeric).
486. Sonified ward monitorable with your ears while doing other tasks.
487. LLM "ward registrar" answering free-text questions over the whole cohort.
488. Federated multi-hospital virtual-ward network learning collectively.
489. Self-explaining model that writes its own incident report after each event.
490. Predict not just deterioration but the most likely *cause*, narrowing the differential.
491. "Recovery coach" mode turning the same data into patient-facing motivation (Challenge-2 crossover).
492. Anomaly-driven auto-zoom re-composing the dashboard around the emerging problem.
493. Causal intervention recommender ranking actions by predicted benefit per patient.
494. Cross-patient contagion detection for infectious/environmental clusters.
495. Topology-of-recovery atlas mapping every patient onto a shared manifold of outcomes.
496. Predictive discharge with a confidence-gated "safe to leave the ward" recommendation.
497. Real-time fairness monitor ensuring alert rates don't skew across demographics.

### AN. Cross-cutting integrations & extras
498. Unified patient timeline merging telemetry, alerts, clinician actions and carer reports in one scroll.
499. "One number" ward health index for a duty-manager glance, drillable to detail.
500. Closed-loop learning where every resolved case improves both prediction and alert routing.
501. Cross-condition transfer so a model trained on one virtual ward bootstraps another.
502. Explainable discharge summary auto-generated from the full stay.
503. Service-level dashboard for how the whole virtual-ward programme is performing.
504. Equity dashboard tracking access and outcomes across populations.
505. Clinician-facing "model changelog" so users know when and how the model updated.
506. Incident-replay tool for M&M review using recorded trajectories.
507. A/B harness comparing two visualisation designs on clinician decision speed.
508. Patient-consent and data-sharing control centre spanning both apps.
509. Severity-weighted handover ordering the next shift's attention list automatically.
510. "Trajectory diff" between admission and now, summarised in one sentence.
511. Configurable clinical-rule engine sitting safely above the ML layer.
512. End-to-end provenance from raw sensor sample to displayed prediction, fully traceable.

---

## PART 2 — THE EVALUATION RUBRIC

Hackathons reward a different shape of idea than a research programme: something a small team can *build a convincing slice of in 24–48 h*, that *demos well in three minutes*, and that *shows real clinical and data-science substance*. The weights below reflect that. Each concept is scored 1–5 per criterion; the composite is the weighted sum rescaled to 0–100 (so the theoretical max is 100).

| # | Criterion | Weight | What a 5 looks like |
|---|-----------|--------|---------------------|
| 1 | **Clinical impact / decision value** | 22 | Changes a real decision — catches deterioration earlier, cuts alarm load, frees capacity. |
| 2 | **Data-science depth & novelty** | 18 | Showcases advanced DS the challenge explicitly invites (state-space, GNNs, survival, causal). |
| 3 | **Visual / UX clarity** | 18 | Makes overwhelming telemetry *instantly* legible — the core mandate of Challenge 3. |
| 4 | **Hackathon feasibility** | 15 | A convincing vertical slice is buildable by a small team in the time available. |
| 5 | **Demo-ability / judge wow** | 12 | Lands a memorable "ah" moment in a short pitch. |
| 6 | **Data availability** | 6 | Buildable now on synthetic or public data, no real-feed dependency. |
| 7 | **Trust / validation / safety** | 5 | Has a credible safety and validation story (honest uncertainty, auditability). |
| 8 | **Challenge-2 bridge** | 4 | Connects cleanly to the carer/family side. |

A deliberately low data-availability weight (6) recognises that *every* concept here is buildable on a synthetic generator (corpus §AB) — so it rarely discriminates, but it would torpedo anything needing a live NHS feed.

---

## PART 3 — THE SYNTHESIS (16 ranked concepts)

Each concept is a *synthesis* — a hero visual + a DS core + a clinical hook — assembled from numbered corpus ideas. Ranked by composite score. Codenames follow the Greek/Egyptian convention.

### Summary scorecard

| Rank | Concept | Impact | DS | Viz | Feas | Demo | Data | Trust | C2 | **Composite** |
|------|---------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | **STYX** — state-space trajectory monitor | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 4 | **94.2** |
| 2 | **TIDE** — survival waterline | 5 | 4 | 5 | 5 | 4 | 5 | 4 | 3 | **91.4** |
| 3 | **ORACLE** — deterioration weather-forecast | 5 | 4 | 5 | 4 | 5 | 5 | 4 | 3 | **90.8** |
| 4 | **ARGUS** — ward-as-constellation triage | 5 | 4 | 5 | 4 | 5 | 5 | 3 | 3 | **89.8** |
| 5 | **CHIRON** — ML-augmented continuous NEWS2 | 5 | 3 | 4 | 5 | 4 | 5 | 5 | 3 | **85.2** |
| 6 | **AEGIS** — silent-deterioration detector | 5 | 4 | 4 | 4 | 4 | 5 | 3 | 3 | **83.8** |
| 7 | **CADUCEUS** — patient-as-graph GNN | 5 | 5 | 4 | 3 | 4 | 4 | 3 | 3 | **83.2** |
| 8 | **JANUS** — counterfactual escalation cockpit | 5 | 5 | 4 | 2 | 5 | 4 | 2 | 3 | **81.6** |
| 9 | **HERMES** — carer–clinician bridge | 4 | 3 | 4 | 4 | 5 | 5 | 3 | 5 | **79.8** |
| 10 | **SENTINEL** — trust-aware sensor-fusion map | 4 | 3 | 4 | 4 | 4 | 5 | 5 | 3 | **77.8** |
| 11 | **CARTOGRAPHER** — Minard ward composite | 3 | 3 | 5 | 4 | 5 | 5 | 3 | 3 | **77.4** |
| 12 | **ECHO** — patient-twin outcome anchoring | 4 | 3 | 4 | 4 | 4 | 5 | 3 | 3 | **75.8** |
| 13 | **MORPHEUS** — recovery-phenotype clustering | 4 | 4 | 4 | 3 | 4 | 5 | 3 | 2 | **75.6** |
| 14 | **TOPOS** — topological recovery atlas | 3 | 5 | 4 | 3 | 4 | 5 | 3 | 2 | **74.8** |
| 15 | **DEMETER** — capacity & discharge optimiser | 4 | 3 | 3 | 4 | 3 | 5 | 3 | 2 | **69.0** |
| 16 | **SONUS** — sonified / ambient ward | 3 | 2 | 4 | 4 | 5 | 5 | 2 | 2 | **68.4** |

---

### 1 — STYX · Patient State-Space Trajectory Monitor — *94.2*
**This is the project the challenge brief describes.** Project each patient's multivariate vitals into a learned 2-D latent space; render the stay as a path with the current position as a live marker; shade the map into a *stability basin* and a *crisis attractor* learned from historical cohorts. The clinician sees, at a glance, whether the patient is drifting toward green or red — and a short forecast cone shows where they're heading next.
- **Hero viz:** the trajectory map with velocity tail, uncertainty tube, and a forecast cone (§1, 2, 3, 11, 12, 101).
- **DS core:** sequential VAE / deep Markov model or latent-ODE for the state, plus a short-horizon forecaster (§258, 259, 261, 206).
- **MVP slice:** one condition, one synthetic ward; 2-D latent map + 4-h forecast cone + basin/attractor shading. A few hundred lines.
- **Demo:** speed-up-time control — judges watch a stable patient orbit the basin, then one patient peel off toward the crisis attractor as the alert fires *hours* before a threshold would.
- **Challenge-2 link:** a simplified, non-alarming family version of the same trajectory (§424).
- **Risk:** the latent space must be *legible*, not a black box — disentangle or label axes (§260) so clinicians read it as physiology.

### 2 — TIDE · Ward Survival Waterline — *91.4*
A horizon "waterline" per patient where the level *is* the model's probability that the patient stays stable over the next 24 h; the tide rising means improving, sinking means deteriorating. Aggregate all levels into one ward tide for the handover glance, and drill into a per-patient survival curve.
- **Hero viz:** the waterline + per-patient stability-survival curve (§34, 226, 33).
- **DS core:** dynamic / landmark survival modelling with time-varying covariates (§220, 224, 225, 228) — squarely in your wheelhouse.
- **MVP slice:** streaming survival probability → animated waterline; landmark Cox on engineered telemetry features.
- **Demo:** the shift-handover glance — one image tells you who's sinking.
- **Why high:** maximally legible, statistically defensible, and fast to validate (time-dependent concordance, calibration).

### 3 — ORACLE · Deterioration Weather-Forecast — *90.8*
Forecast the next N hours as a *hurricane cone* — a most-likely path plus a probability envelope — and fire alerts when the cone crosses a threshold, not when the patient already has. Honest uncertainty is the differentiator: the cone narrows when the model is confident, widens when it isn't.
- **Hero viz:** the forecast cone with quantile bands (§101, 102, 108, 109).
- **DS core:** mixture-density or quantile forecaster wrapped in conformal prediction for guaranteed coverage (§213, 112, 208).
- **MVP slice:** one signal-set forecaster + cone + predictive alert.
- **Demo:** the cone bends and widens toward crisis; the alert fires early; contrast with a reactive threshold that fires too late.
- **Trust:** conformal intervals give judges a rigorous safety story.

### 4 — ARGUS · Ward-as-Constellation Triage — *89.8*
Directly attacks the "telemetry overwhelms dashboards" problem at *ward* scale. Every patient is a glyph in shared latent space; the roster sorts by time-to-likely-escalation; deteriorating patients catch the eye by *motion* alone.
- **Hero viz:** the animated constellation + a heat-strip roster (§19, 22, 23, 20).
- **DS core:** shared-latent trajectory embedding (§266, 204) + time-to-event ranking (§220).
- **MVP slice:** 20 synthetic patients, animated constellation, ranked roster.
- **Demo:** one star streaks toward red across a calm field — the clinician's eye goes straight to it. Pairs beautifully as the cohort-level view *on top of* STYX's patient-level view.

### 5 — CHIRON · ML-Augmented Continuous NEWS2 — *85.2*
The pragmatic, NHS-credible play. Compute NEWS2 *continuously* from streaming telemetry instead of intermittent spot-checks, then layer an ML uplift that buys lead time — and show clinicians where score and model *agree* or *disagree*.
- **Hero viz:** continuous NEWS2 trace + ML overlay + a "lead-time gained" number (§387, 388, 392, 478).
- **DS core:** hybrid score-as-feature model (§211) with the precision/recall trade-off made visible (§215).
- **Demo:** lead-time gained vs spot-check NEWS2, quantified.
- **Why it ranks well:** highest feasibility + trust scores; easy to validate; speaks the judges' language. Lower DS-novelty ceiling, hence mid-rank.

### 6 — AEGIS · Silent-Deterioration Detector — *83.8*
Targets the clinical nightmare: the patient whose absolute numbers look fine but whose *trend* is adverse. Learn each patient's own normal in the first hours and flag departures from *their* baseline plus change-points — catching deterioration before population thresholds would.
- **Hero viz:** the personal-normal ribbon + a "silent deterioration" flag (§41, 47, 382).
- **DS core:** personalised one-class anomaly + change-point detection (§234, 236, 376, 381).
- **Demo:** a patient comfortably "in range" gets flagged before any standard alarm.
- **Strength:** clinically compelling and conceptually crisp; modest viz wow holds it below the top tier.

### 7 — CADUCEUS · Patient-as-Graph GNN — *83.2*
**The highest-ceiling data-science concept, and the one the brief most directly invites.** Model each patient as a graph of physiological subsystems (cardiac, respiratory, renal…); a graph-attention network predicts deterioration *and* shows which subsystem *coupling* is driving risk — interpretable by construction.
- **Hero viz:** the patient graph with edge-attention lighting up the coupling that's failing (§182, 191), plus a ward-level patient-similarity graph (§180).
- **DS core:** lightweight spatio-temporal GraphSAGE / GAT with recurrent node states (§177, 178, 183, 192).
- **MVP slice:** a few-layer GNN on synthetic multi-signal data; graph viz with attention weights.
- **Demo:** the cardio-respiratory edge lights up *before* either single-signal alarm — "the model saw the systems decoupling first."
- **Why ranked #7 not #1:** pure hackathon feasibility is the risk — GNNs need careful data plumbing and can underperform a strong sequence model in 24–48 h. **But its DS ceiling is the highest here, and it combines superbly with STYX** (latent trajectory shows *where*; the graph shows *why*). If your team has GNN comfort, promote it.

### 8 — JANUS · Counterfactual Escalation Cockpit — *81.6*
Decision support with a twist judges remember: a panel that recommends *observe / escalate / discharge* and shows the **counterfactual** — "if you wait 4 h, risk rises to X" — as a ghost trail beside the actual trajectory.
- **Hero viz:** the decision card + counterfactual ghost trail (§13, 271, 275, 335).
- **DS core:** a safety-constrained policy (POMDP framing) evaluated off-policy on historical/synthetic data (§329, 330, 334) + counterfactual forecasting.
- **Demo:** "here's what happens if you wait" — visceral and memorable.
- **Risk:** highest build difficulty and the thinnest validation story of the top group; demo wow is high but feasibility drags it down. Strong as a *stretch* feature layered onto STYX or ORACLE.

### 9 — HERMES · Carer–Clinician Bridge — *79.8*
The explicit Challenge-2 link, done well: **one state model, two views.** The clinician sees the full trajectory and risk drivers; the carer simultaneously sees a plain-language card — "watch for X, we're monitoring, things are stable" — and their observations feed back as soft model inputs.
- **Hero viz:** split-screen clinician trajectory ↔ carer plain-language card (§411, 412, 413, 424).
- **DS core:** shared latent state + an NLG layer turning risk drivers into lay guidance (§128, 305).
- **Demo:** clinician risk spikes; the carer view shows calm, confidence-appropriate guidance — never over-alarming.
- **Why include it:** directly answers "be considerate of Challenge 2," and the *shared underlying model* is the elegant insight. Best deployed as a thin slice on top of STYX/TIDE rather than a standalone build.

### 10 — SENTINEL · Trust-Aware Sensor-Fusion Map — *77.8*
Surfaces data quality and model confidence alongside every prediction, so clinicians know *when to trust* and the system degrades gracefully. A dropped sensor says "check sensor," never silently reads as normality.
- **Hero viz:** confidence + quality overlay on predictions; missingness ribbon (§35, 103, 107, 114, 116).
- **DS core:** per-window quality indices gating conformal-confidence outputs (§290, 120, 112).
- **Demo:** pull a sensor mid-demo; the system honestly downgrades and prompts a fix — the *opposite* of fabricated precision.
- **Strength:** best trust/safety score; a superb *feature* to fold into the winner rather than a headline on its own.

### 11 — CARTOGRAPHER · Minard Ward Composite — *77.4*
Your signature aesthetic as a deliverable: a single high-density Minard-style canvas summarising the whole ward's last 24 h — flows for stability, colour for risk, annotations for interventions — print-friendly for handover.
- **Hero viz:** the Minard composite + a ward state-transition Sankey (§62, 63, 64, 66).
- **DS core:** lighter — state-transition modelling + risk ribbons (§250, 65).
- **Demo:** the poster *is* the demo; instantly distinctive visual identity.
- **Trade-off:** unmatched viz, lower DS depth — strongest as the *report/handover artifact* of whichever engine wins.

### 12 — ECHO · Patient-Twin Outcome Anchoring — *75.8*
Surface the most-similar past patients and their *outcomes* as decision anchors: "your patient looks like these three — two recovered, one needed escalation." Case-based reasoning that complements any predictor.
- **Hero viz:** twin overlays with outcome labels (§17, 91, 98, 131).
- **DS core:** trajectory embedding + similarity search (§204, 316).
- **Demo:** intuitive and immediately trusted by clinicians who think in cases.

### 13 — MORPHEUS · Recovery-Phenotype Clustering — *75.6*
Discover recovery archetypes (fast / slow / relapsing), place the live patient among them, and forecast using the model specialised to that phenotype. Phenotype *switching* becomes an early-warning event in itself.
- **Hero viz:** the phenotype landscape with the patient's placement (§193, 195, 200).
- **DS core:** DTW or latent-mixture trajectory clustering (§194, 195, 199).
- **Demo:** "this patient matches the slow-relapsing phenotype, which typically needs review at day 3."

### 14 — TOPOS · Topological Recovery Atlas — *74.8*
The most novel DS concept: persistent homology and Mapper on patient trajectories. Loss of a stable physiological *cycle* (a topological signature) becomes an early-warning marker, and a cohort Mapper graph reveals the branch points between recovery and decline.
- **Hero viz:** the Mapper cohort graph + per-patient topological signature (§307, 311, 306).
- **DS core:** a giotto-tda pipeline — persistence features feeding the predictor (§308, 309, 315).
- **Demo:** topology shifts *before* any single signal does.
- **Trade-off:** distinctive and high DS-novelty, but niche legibility for clinicians and the steepest "explain it in 3 minutes" curve — hence mid-rank for a hackathon despite its depth.

### 15 — DEMETER · Capacity & Discharge Optimiser — *69.0*
The system-level value play: predict step-down/discharge readiness to free monitoring capacity, with a ward-capacity forecast for duty managers.
- **Hero viz:** discharge-readiness leaderboard + capacity forecast (§30, 399, 401).
- **DS core:** readiness model + survival-based discharge timing (§231, 408).
- **Trade-off:** appeals to service/operations judges; less individual-patient drama, lower demo wow.

### 16 — SONUS · Sonified / Ambient Ward — *68.4*
The wildcard: monitor the ward by *ear*. Rising risk subtly raises a tone; a wall display shows the constellation for passive monitoring. Judges literally *hear* a patient deteriorate.
- **Hero viz:** the constellation wall + sonification (§144, 486, 141).
- **DS core:** thin — risk scoring feeding an audio mapping.
- **Trade-off:** highest novelty-of-modality and a real "wow," but shallow DS — a memorable garnish, not a main course.

---

## IF YOU BUILD ONE THING

**Build STYX as the spine, with one DS showpiece and one thin Challenge-2 slice.** Concretely:

- **Spine — STYX (#1):** the latent state-space trajectory map with basin/attractor shading and a forecast cone. This *is* the challenge's headline ask and the most memorable single visual.
- **DS showpiece — pick one by your team's comfort:**
  - **CADUCEUS (#7)** if you have GNN confidence — the graph shows *why* the patient is moving, the brief explicitly invites GNNs, and "the model saw the systems decouple first" is a killer line. Highest ceiling.
  - **ORACLE (#3)** if you want a safer, equally striking option — the forecast cone with conformal uncertainty is rigorous and lands instantly.
- **Trust layer — fold in SENTINEL (#10):** quality-gated, honest-uncertainty outputs. Cheap to add, and it pre-empts the judges' "but can you trust it?" question.
- **Challenge-2 slice — a thin HERMES (#9):** one carer-facing screen reading the *same* state model in plain language. A small build that demonstrably honours "be considerate of Challenge 2."
- **Demo engine — a synthetic generator (§AB / #353, 364):** scripted deterioration scenarios you can replay and speed up. This de-risks the entire demo and is something you've built before.

**Two combination plays worth naming:**
1. **STYX + ARGUS** — patient-level trajectory *and* the ward-level constellation built on the same shared latent space. One embedding, two scales: the strongest pure-Challenge-3 story.
2. **STYX + CADUCEUS** — trajectory (*where* the patient is going) plus the physiological graph (*why*). The most complete data-science narrative, if feasibility allows.

**A note on your existing assets** (these meaningfully de-risk specific concepts): the trajectory-visualisation work in ST-P maps almost directly onto STYX's hero view; your survival-modelling stack (Cox PH / DeepSurv) is exactly TIDE and ORACLE; your synthetic-data experience (SEKHMET, copula-based generators) is the demo engine; your giotto-tda assessment is TOPOS ready-made; and your Minard work is CARTOGRAPHER. The hackathon-shaped move is a vertical slice in RAIE style — synthetic data first, `seed=42`, one condition, one killer view, an `EXPERIMENT_LOG.md` — and let the visual carry the pitch.
