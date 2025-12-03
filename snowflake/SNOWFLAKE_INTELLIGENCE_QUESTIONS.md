# Snowflake Intelligence Questions

Sample questions for use with Snowflake Intelligence after wiring **both** Cortex Search and Cortex Analyst.

This demo showcases the complementary power of:
- **🔍 Cortex Search** → Semantic similarity on free-text descriptions ("Find issues similar to...")
- **📊 Cortex Analyst** → Structured SQL analytics ("How many?", "Average of?")

The maintenance requests now include **realistic free-text descriptions** like:
- *"Light flickering on and off throughout the night. Very annoying for nearby houses."*
- *"Exposed wires visible near the pole base. Dangerous situation, needs urgent attention."*
- *"Pole leaning dangerously after vehicle collision. Immediate attention needed!"*

Copy and paste these natural language questions directly into the Snowflake Intelligence chat interface.

---

## Quick Reference: Which Capability Handles What?

| Question Type | Best Capability | Example |
|--------------|-----------------|---------|
| Semantic similarity | 🔍 Search | "Find issues similar to water damage" |
| Free-text matching | 🔍 Search | "Show me complaints about flickering" |
| Count/aggregate | 📊 Analyst | "How many lights are faulty?" |
| Averages/sums | 📊 Analyst | "Average resolution time?" |
| Fuzzy concept search | 🔍 Search | "Find safety hazards" |
| Exact filters | 📊 Analyst | "Which neighborhood has most issues?" |

---

## Category 1: Semantic Search on Descriptions 🔍

*Cortex Search excels at finding semantically similar descriptions*

**Water & Weather Damage:**
- "Find issues related to water damage or flooding"
- "Show me maintenance requests mentioning rain or storm"
- "What issues mention monsoon weather?"
- "Find problems caused by lightning"

**Safety Hazards:**
- "Show me safety hazard reports"
- "Find dangerous situations that need urgent attention"
- "What requests mention fire risk or sparking?"
- "Show me exposed wire issues"

**Flickering & Intermittent Issues:**
- "Find lights that flicker on and off"
- "Show me intermittent power problems"
- "What issues mention dim or fading lights?"
- "Find complaints about buzzing or noise"

**Vehicle & Physical Damage:**
- "Show me vehicle collision damage"
- "Find poles that are leaning or bent"
- "What issues mention accidents?"
- "Show me vandalism reports"

---

## Category 2: Equipment Problems 🔍

*Cortex Search finds issues by semantic meaning in descriptions*

**Electrical Issues:**
- "Find issues with loose connections"
- "Show me short circuit problems"
- "What requests mention overheating?"
- "Find electrical arcing reports"

**Sensor & Controller Issues:**
- "Show me sensor malfunction reports"
- "Find issues where light stays on during daytime"
- "What problems mention timer failures?"
- "Show me smart controller issues"

**Structural Problems:**
- "Find corrosion or rust damage"
- "Show me termite or pest damage"
- "What issues mention foundation problems?"
- "Find reports of structural weakness"

---

## Category 3: Analytics Questions 📊

*Cortex Analyst handles aggregations and counts*

- "How many maintenance requests are currently open?" 📊
- "What are the most common issue types?" 📊
- "Which neighborhoods have the most maintenance issues?" 📊
- "What is the average resolution time by issue type?" 📊
- "How many lights need repair by status?" 📊

---

## Category 4: Urgency & Resident Complaints 🔍

*Search finds urgency language in descriptions*

- "Find requests marked as urgent or immediate"
- "Show me complaints from residents"
- "What issues mention safety concerns?"
- "Find reports that say 'needs immediate attention'"
- "Show me issues described as dangerous"

---

## Category 5: Technical Root Causes 🔍

*Search for diagnostic details in descriptions*

- "Find issues mentioning thermal problems"
- "Show me reports about voltage fluctuation"
- "What issues mention cable or wire damage?"
- "Find problems related to transformers"
- "Show me reports about power theft"

---

## Category 6: Seasonal & Environmental 🔍

*Search finds weather-related descriptions*

- "Find issues caused by heavy rain"
- "Show me heat-related problems"
- "What issues mention extreme temperatures?"
- "Find waterlogging or flooding damage"
- "Show me cold weather issues"

---

## Category 7: Supplier & Dispatch

- "Which supplier should handle this repair?"
- "Find the nearest technician for this issue"
- "Show me issues that need specialized equipment"
- "Which repairs require an electrician?"
- "What parts are needed for pending repairs?"

---

## Category 8: Analytics & Reporting 📊

*Best handled by Cortex Analyst*

- "What's the average time to fix a bulb failure?"
- "How many lights are currently not working?"
- "Show me maintenance trends over time"
- "Which types of issues take longest to resolve?"
- "What percentage of lights need maintenance?"

---

## Top 10 Demo Questions

Best questions for live demo - showing **Search vs Analyst** distinction:

### Cortex Search (Semantic Similarity) 🔍

1. "Find issues that mention flickering or blinking" 
   → *Searches free-text descriptions*

2. "Show me safety hazards and dangerous situations"
   → *Finds semantic matches like "fire hazard", "exposed wires"*

3. "Find complaints about lights staying on during daytime"
   → *Matches sensor malfunction descriptions*

4. "Show me reports similar to water damage"
   → *Semantic similarity to flooding, rain, corrosion*

5. "Find vehicle collision damage to poles"
   → *Matches accident-related descriptions*

### Cortex Analyst (SQL Analytics) 📊

6. "How many maintenance requests are currently open?"
   → *Returns exact count*

7. "Which neighborhoods have the most issues?"
   → *Aggregation by location*

8. "What is the average resolution time by issue type?"
   → *Computed metric*

9. "What are the most common issue types?"
   → *Group by and count*

10. "How many lights are faulty vs operational?"
    → *Status breakdown*

---

## Tips for Follow-up Questions

After getting initial results, try these follow-up questions:

- "Show me more details about the first one"
- "Which supplier is closest to that location?"
- "How long did similar issues take to fix?"
- "What's the resolution status?"
- "Show me the history for this light"

---

## Combined Queries (Advanced)

These questions combine multiple data sources:

- "Show me high-risk lights with their nearest supplier"
- "Find urgent issues in neighborhoods with high population"
- "Which faulty lights have the longest wait time?"
- "Show me weather damage in areas with frequent outages"
- "Find repeated failures and their common causes"

---

## Cortex Analyst Specific Questions 📊

These analytical questions work best with the semantic model:

### Infrastructure Metrics
- "How many street lights do we have by status?"
- "What is the total power consumption by neighborhood?"
- "Show me lights per neighborhood ranked by count"
- "What's the average wattage across all lights?"

### Resolution Analytics
- "What is the average resolution time for each issue type?"
- "Which issue types take longest to resolve?"
- "How many requests are resolved vs still open?"
- "What's the median resolution time this month?"

### Weather & Risk
- "What is the average failure risk by season?"
- "How many lights have risk scores above 0.7?"
- "Which season has the highest average rainfall?"
- "Show me predicted failures for next 30 days"

### Power Grid Analytics
- "Which power grid zones have the most outages?"
- "What's the average grid load by zone?"
- "Correlate outage count with failure risk"

### Supplier Performance
- "What are the average response times by supplier?"
- "How many suppliers by specialization?"
- "Which suppliers cover the largest radius?"

### Demographics
- "How are lights distributed across urban vs rural areas?"
- "What's the population per street light by neighborhood?"
- "Show population density vs maintenance request count"

### CDC Monitoring
- "Show me records modified today via CDC"
- "Which tables have the most recent changes?"
- "How many records synced in the last hour?"

---

## Demo Flow: Search + Analyst Together

For the best demo experience, show how both capabilities complement each other.
**Key insight**: Search finds *similar* records by meaning, Analyst computes *aggregates*.

### Scenario: Safety Audit

1. **🔍 Search**: "Find safety hazards and dangerous situations"
   → Returns: *"Exposed wires visible near pole base. Dangerous situation..."*
   → Returns: *"Sparking observed from junction box during rain. Fire hazard!"*

2. **📊 Analyst**: "How many open requests mention wiring issues?"
   → Get exact count for report

3. **🔍 Search**: "Show me issues similar to fire risk"
   → Finds related electrical hazards by semantic similarity

4. **📊 Analyst**: "Which neighborhoods have the most wiring issues?"
   → Prioritize inspection areas

### Scenario: Monsoon Preparation

1. **📊 Analyst**: "What is the average failure risk by season?"
   → See monsoon has highest risk

2. **🔍 Search**: "Find issues caused by rain, flooding, or water damage"
   → Returns: *"Water ingress in wire conduit. Corrosion visible..."*
   → Returns: *"Underground cable damaged by flooding..."*

3. **📊 Analyst**: "How many maintenance requests occurred during monsoon?"
   → Quantify seasonal impact

4. **🔍 Search**: "Show me lightning strike damage reports"
   → Find specific storm-related incidents

### Scenario: Vehicle Damage Investigation

1. **🔍 Search**: "Find vehicle collision or accident damage"
   → Returns: *"Pole leaning dangerously after vehicle collision..."*
   → Returns: *"Pole hit by truck. Bent at 45 degree angle..."*

2. **📊 Analyst**: "How many pole damage issues are currently open?"
   → Count for insurance/reporting

3. **🔍 Search**: "Show me structural problems and leaning poles"
   → Find related stability issues
