# Rep Narrative Content Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `narrative` field to each representative and build a Claude Code workflow that researches and writes storytelling narratives for all 538 members of Congress.

**Architecture:** Two model fields (`narrative`, `narrative_updated`) on `Representative`, a template section to display narratives, and a Claude Code scheduled task that does web research + writing per state. The prompt template lives in `reps/prompts/narrative_prompt.md` so non-engineers can edit the tone.

**Tech Stack:** Django 6.0, SQLite (local), Claude Code scheduled tasks, web search

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `reps/models.py` | Modify | Add `narrative` and `narrative_updated` fields |
| `reps/admin.py` | Modify | Add narrative to `search_fields`, make editable for rewrites |
| `reps/templates/reps/detail.html` | Modify | Add "The Story" section after header card |
| `reps/migrations/0002_representative_narrative.py` | Create (auto) | Migration for new fields |
| `reps/prompts/narrative_prompt.md` | Create | Prompt template for narrative generation |

The scheduled task will be created via the `create_scheduled_task` MCP tool, not as a file we write manually.

---

## Chunk 1: Data Model + Display

### Task 1: Add narrative fields to Representative model

**Files:**
- Modify: `reps/models.py:52-55` (after `alignment_score`, before `last_updated`)

- [ ] **Step 1: Add the two fields**

In `reps/models.py`, add after the `alignment_score` field (line 53) and before `last_updated` (line 55):

```python
    # Narrative content
    narrative = models.TextField(blank=True, default="")
    narrative_updated = models.DateTimeField(null=True, blank=True)
```

- [ ] **Step 2: Generate migration**

Run:
```bash
cd /Users/adamlinssen/Desktop/the80percentbill
DJANGO_SETTINGS_MODULE=the_80_percent_bill.settings DEBUG=true python3 manage.py makemigrations reps -n representative_narrative
```
Expected: `reps/migrations/0002_representative_narrative.py` created

- [ ] **Step 3: Apply migration**

Run:
```bash
DJANGO_SETTINGS_MODULE=the_80_percent_bill.settings DEBUG=true python3 manage.py migrate reps
```
Expected: `Applying reps.0002_representative_narrative... OK`

- [ ] **Step 4: Verify in shell**

Run:
```bash
DJANGO_SETTINGS_MODULE=the_80_percent_bill.settings DEBUG=true python3 -c "
import django; django.setup()
from reps.models import Representative
r = Representative.objects.first()
print('narrative:', repr(r.narrative))
print('narrative_updated:', r.narrative_updated)
"
```
Expected: `narrative: ''` and `narrative_updated: None`

- [ ] **Step 5: Commit**

```bash
git add reps/models.py reps/migrations/0002_representative_narrative.py
git commit -m "feat(reps): add narrative and narrative_updated fields to Representative"
```

---

### Task 2: Update admin to include narrative

**Files:**
- Modify: `reps/admin.py:7-11`

- [ ] **Step 1: Update RepresentativeAdmin**

In `reps/admin.py`, update the `RepresentativeAdmin` class:

```python
@admin.register(Representative)
class RepresentativeAdmin(admin.ModelAdmin):
    list_display = ["full_name", "party", "state", "chamber", "in_office"]
    list_filter = ["party", "chamber", "state", "in_office"]
    search_fields = ["first_name", "last_name", "full_name", "bioguide_id", "state", "narrative"]
    readonly_fields = ["last_updated", "narrative_updated"]
```

Note: `narrative` is NOT in `readonly_fields` — it stays editable so someone can blank it to trigger a rewrite. It is NOT in `list_display` — too large for the list view.

- [ ] **Step 2: Commit**

```bash
git add reps/admin.py
git commit -m "feat(reps): add narrative to admin search fields"
```

---

### Task 3: Add "The Story" section to detail template

**Files:**
- Modify: `reps/templates/reps/detail.html:20-22`

- [ ] **Step 1: Insert narrative section**

In `reps/templates/reps/detail.html`, insert the following block after line 20 (`</div>` closing `rep-header-card`) and before line 22 (`<!-- Alignment score -->`):

```html

<!-- The Story -->
<div class="rep-section">
    <h2>The Story</h2>
    {% if rep.narrative %}
    <div class="rep-narrative">
        {{ rep.narrative|linebreaks }}
    </div>
    {% else %}
    <div class="note-text">Profile narrative coming soon.</div>
    {% endif %}
</div>

```

- [ ] **Step 2: Verify in browser**

Run the dev server if not already running:
```bash
DEBUG=true python3 manage.py runserver 8000
```

Visit `http://127.0.0.1:8000/reps/B001323/` (Nicholas Begich). Should see "Profile narrative coming soon." between the header card and alignment score.

- [ ] **Step 3: Commit**

```bash
git add reps/templates/reps/detail.html
git commit -m "feat(reps): add narrative section to detail page"
```

---

## Chunk 2: Prompt Template + Scheduled Task

### Task 4: Create the narrative prompt template

**Files:**
- Create: `reps/prompts/narrative_prompt.md`

- [ ] **Step 1: Create the prompts directory and file**

Create `reps/prompts/narrative_prompt.md` with this content:

````markdown
# Representative Narrative — Research & Writing Prompt

You are writing a profile narrative for a member of Congress through the lens of the 80% Bill.

## Representative

- **Name:** {full_name}
- **Title:** {title}
- **Party:** {party}
- **State/District:** {district_display}
- **Chamber:** {chamber}
- **Term:** {term_start} to {term_end}
- **Official Website:** {official_website}
- **OpenSecrets ID:** {opensecrets_id}
- **GovTrack ID:** {govtrack_id}

## The 80% Bill

The 80% Bill is a package of 20 policies that 80%+ of Americans agree on, regardless of party. Here are the bills:

{bill_list}

## Research Instructions

For this representative, search for:

1. **Cosponsorship and voting history** on the 20 bills listed above, or closely related legislation
2. **Top campaign donors** — search OpenSecrets for their donor profile
3. **Committee assignments** — what committees do they sit on and how does that relate to the 20 bills?
4. **Public statements** — have they spoken publicly about any of the 80% Bill topics?
5. **Contradictions** — do their donors oppose policies they claim to support? Do their votes contradict their public statements?

If you cannot find information on a topic, skip it. Do NOT speculate or fabricate.

## Writing Instructions

Write a 3-5 paragraph narrative that tells this representative's story through the lens of the 80% Bill.

### Tone

Write like a well-researched political satirist. The facts are sacred — never exaggerate or fabricate. But how you present those facts can be pointed, ironic, and occasionally biting. If a rep talks about fighting corruption while their top donor is a corporate PAC, let the irony land. Don't editorialize with opinions — let the contradictions speak for themselves.

Imagine you're a journalist writing a fair but unflinching profile. The reader should walk away understanding where this person stands and why.

### Structure

- **Paragraph 1:** Who they are — name, party, district, how long they've served, what they're known for
- **Paragraph 2-3:** Where they stand on the 80% Bill topics — what have they supported, opposed, or ignored? What do their votes and cosponsorship records show?
- **Paragraph 4:** Follow the money — who funds them and how does that align (or conflict) with their stated positions?
- **Paragraph 5 (optional):** The bottom line — a concise, pointed summary of what their record tells us

### Rules

- Every claim must be based on something you found in your research
- Name specific bills, vote dates, and donor amounts when you find them
- Do not use headers, bullet points, or markdown formatting — write in flowing paragraphs
- Do not include citations or URLs in the text — keep it clean prose
- Keep total length to 300-500 words
````

- [ ] **Step 2: Commit**

```bash
git add reps/prompts/narrative_prompt.md
git commit -m "feat(reps): add narrative prompt template"
```

---

### Task 5: Create the scheduled task

This task uses the `create_scheduled_task` tool to register a Claude Code scheduled task. The key design: the **orchestrator** queries for reps that need narratives, then **dispatches one subagent per representative** to do the research and writing in parallel.

- [ ] **Step 1: Create the scheduled task**

Use the `create_scheduled_task` MCP tool with:

- **taskId:** `generate-rep-narratives`
- **description:** `Research and write narrative profiles for congressional representatives, one state at a time`
- **prompt:** (see below)

The prompt for the scheduled task:

```
You are the orchestrator for generating narrative content for congressional representative profile pages on the 80% Bill website.

## Setup

Working directory for all commands: cd /Users/adamlinssen/Desktop/the80percentbill

1. Read the prompt template at reps/prompts/narrative_prompt.md — this defines the tone, structure, and research instructions for each narrative.
2. Read the bill articles from bill/articles.py — extract the ARTICLES list and format each entry as "N. Title — Description" for inclusion in subagent prompts.
3. Query the database to find which states still need narratives:

cd /Users/adamlinssen/Desktop/the80percentbill && DJANGO_SETTINGS_MODULE=the_80_percent_bill.settings DEBUG=true python3 -c "
import django; django.setup()
from reps.models import Representative
states = Representative.objects.filter(in_office=True, narrative='').values_list('state', flat=True).distinct().order_by('state')
for s in states:
    count = Representative.objects.filter(state=s, in_office=True, narrative='').count()
    print(f'{s}: {count} remaining')
"

4. Pick the next state alphabetically that still has reps without narratives.
5. Get the list of bioguide IDs for that state:

cd /Users/adamlinssen/Desktop/the80percentbill && DJANGO_SETTINGS_MODULE=the_80_percent_bill.settings DEBUG=true python3 -c "
import django; django.setup()
from reps.models import Representative
reps = Representative.objects.filter(in_office=True, narrative='', state='STATE_CODE').order_by('last_name')
for r in reps:
    print(f'{r.bioguide_id} — {r.full_name} ({r.get_party_display()}, {r.district_display})')
"

## Dispatch subagents

For each representative in the state, dispatch a subagent using the Agent tool with:
- subagent_type: "general-purpose"
- run_in_background: true (so multiple can run in parallel)

Dispatch them in batches of 3-5 at a time to avoid overwhelming the system.

Each subagent's prompt should include:
- The rep's bioguide_id, full name, party, district, chamber, term dates, website, OpenSecrets ID, GovTrack ID
- The full list of 20 bill articles (titles and descriptions)
- The tone guide and writing instructions from the prompt template
- Instructions to:
  1. Do web searches to research the representative's positions on the 20 bills
  2. Search for their top campaign donors
  3. Search for committee assignments and public statements
  4. Write a 3-5 paragraph narrative (300-500 words) following the tone guide
  5. Save the result to the database via:

cd /Users/adamlinssen/Desktop/the80percentbill && DJANGO_SETTINGS_MODULE=the_80_percent_bill.settings DEBUG=true python3 -c "
import django; django.setup()
from django.utils import timezone
from reps.models import Representative
rep = Representative.objects.get(bioguide_id='BIOGUIDE_ID')
rep.narrative = '''NARRATIVE_TEXT_HERE'''
rep.narrative_updated = timezone.now()
rep.save(update_fields=['narrative', 'narrative_updated'])
print(f'Saved narrative for {rep.full_name}')
"

## Selective rewrite mode

If you need to rewrite a specific rep's narrative (e.g., because the first version was inaccurate), blank it first then re-run:

cd /Users/adamlinssen/Desktop/the80percentbill && DJANGO_SETTINGS_MODULE=the_80_percent_bill.settings DEBUG=true python3 -c "
import django; django.setup()
from reps.models import Representative
rep = Representative.objects.get(bioguide_id='TARGET_BIOGUIDE_ID')
rep.narrative = ''
rep.narrative_updated = None
rep.save(update_fields=['narrative', 'narrative_updated'])
print(f'Blanked narrative for {rep.full_name} — will be re-generated on next run')
"

Then dispatch a single subagent for that rep, or run the full state workflow (it will only pick up reps with empty narratives).

## After all subagents complete

Wait for all subagents to finish, then report:
- How many narratives were generated
- Which state was completed
- Any failures (reps that couldn't be researched)
```

- [ ] **Step 2: Verify task was created**

Use `list_scheduled_tasks` to confirm `generate-rep-narratives` exists.

- [ ] **Step 3: Read and verify the generated SKILL.md**

Read `.claude/scheduled-tasks/generate-rep-narratives/SKILL.md` to verify it contains the correct prompt. This is an ad-hoc task (no cron schedule) — it runs only when manually invoked, which is what we want since narrative generation needs human oversight.

- [ ] **Step 4: Commit the generated files**

```bash
git add -A .claude/scheduled-tasks/
git commit -m "feat(reps): add generate-rep-narratives scheduled task"
```

---

### Task 6: Test the full workflow on one representative

- [ ] **Step 1: Manually run the workflow for one rep**

Pick a well-known representative (e.g., Nancy Pelosi, `P000197`) and manually execute the workflow:
- Read their data from the database
- Do web research on their positions on the 20 bills, donors, committees
- Write a narrative following the prompt template's tone and structure
- Save it to the database using the Django shell command from the scheduled task

- [ ] **Step 2: Verify in browser**

Visit their detail page at `http://127.0.0.1:8000/reps/P000197/` and confirm:
- The narrative displays in the "The Story" section
- Paragraphs are properly formatted (not a wall of text)
- The section appears between the header card and alignment score

---

### Task 7: Final commit and push

- [ ] **Step 1: Push all changes**

```bash
git push origin feature/reps-mvp
```

- [ ] **Step 2: Verify progress tracking query works**

```bash
DJANGO_SETTINGS_MODULE=the_80_percent_bill.settings DEBUG=true python3 -c "
import django; django.setup()
from reps.models import Representative
total = Representative.objects.filter(in_office=True).count()
done = Representative.objects.filter(in_office=True).exclude(narrative='').count()
print(f'Progress: {done}/{total} narratives generated')
"
```

Expected: `Progress: 1/538 narratives generated` (after the test run)
