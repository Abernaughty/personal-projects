import requests
import anthropic
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime


MUSE_API_KEY = "YOUR_MUSE_API_KEY"
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"

muse_client = requests.Session()
muse_client.headers.update({"X-Muse-Api-Key": ""}) # MUSE_API_KEY})

anthropic_client = anthropic.Anthropic() # api_key=ANTHROPIC_API_KEY)


def fetch_jobs(categories, levels, location, page=1):
    params = [("page", page), ("location", location)]
    for cat in categories:
        params.append(("category", cat))
    for level in levels:
        params.append(("level", level))

    response = muse_client.get(
        "https://www.themuse.com/api/public/jobs",
        params=params
    )
    response.raise_for_status()
    return response.json()


def strip_html(html_content):
    """Strip HTML tags and clean up whitespace."""
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator="\n")
    # Collapse excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


def extract_skills_and_requirements(job_text):
    """Use Claude to extract structured skills and requirements from job description."""
    prompt = f"""Extract the skills and requirements from this job posting. 
Return ONLY a JSON object with exactly these two keys:
- "skills": a comma-separated string of technical skills and tools mentioned (e.g. "Python, Terraform, AWS, Docker")
- "requirements": a comma-separated string of qualifications and requirements (e.g. "3+ years experience, Bachelor's degree, Azure certification")

If nothing is found for either field, use an empty string.

Job posting:
{job_text[:3000]}"""

    message = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Extract just the JSON object, ignoring any surrounding text
    match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if not match:
        print(f"Warning: Could not find JSON in response: {raw[:200]}")
        return {"skills": "", "requirements": ""}

    try:
        return json.loads(match.group())
    except json.JSONDecodeError as e:
        print(f"Warning: JSON parse failed: {e}\nRaw: {raw[:200]}")
        return {"skills": "", "requirements": ""}


def parse_job(job):
    """Map a Muse API job object to your spreadsheet columns."""
    locations = ", ".join(loc["name"] for loc in job.get("locations", []))
    posted_date = job.get("publication_date", "")
    if posted_date:
        posted_date = datetime.fromisoformat(posted_date.replace("Z", "+00:00")).strftime("%Y-%m-%d")

    clean_description = strip_html(job.get("contents", ""))
    extracted = extract_skills_and_requirements(clean_description)

    return {
        # --- Direct API mappings ---
        "Position":                     job.get("name", ""),
        "Company":                      job.get("company", {}).get("name", ""),
        "Location":                     locations,
        "Posted Date":                  posted_date,
        "URL":                          job.get("refs", {}).get("landing_page", ""),
        "Source":                       "The Muse",
        "Experience Level":             ", ".join(l["name"] for l in job.get("levels", [])),
        "Job Description / Responsibilities": clean_description,
        "Skills":                       extracted.get("skills", ""),
        "Requirements":                 extracted.get("requirements", ""),

        # --- No API equivalent, left blank for manual entry ---
        "Salary":           "",
        "Status":           "",
        "Contact":          "",
        "Application Date": "",
        "I1":               "",
        "I2":               "",
        "I3":               "",
        "Followup Date":    "",
        "Last Contact Date":"",
        "Offer":            "",
        "Feedback":         "",
        "Result":           "",
    }


def fetch_all_jobs(categories, levels, location):
    """Fetch all pages and return a flat list of parsed job dicts."""
    all_jobs = []
    first_page = fetch_jobs(categories, levels, location, page=1)
    total_pages = first_page.get("page_count", 1)

    print(f"Found {first_page.get('total', 0)} jobs across {total_pages} pages")

    for result in first_page.get("results", []):
        all_jobs.append(parse_job(result))

    for page_num in range(2, total_pages + 1):
        print(f"Fetching page {page_num}/{total_pages}...")
        page_data = fetch_jobs(categories, levels, location, page=page_num)
        for result in page_data.get("results", []):
            all_jobs.append(parse_job(result))

    return all_jobs


if __name__ == "__main__":
    jobs = fetch_all_jobs(
        categories=["Computer and IT", "IT"],
        levels=["Entry Level", "Mid Level"],
        location="Colorado Springs, CO"
    )

    print(f"\nParsed {len(jobs)} jobs")
    for job in jobs[:3]:  # Preview first 3
        print(f"\n--- {job['Position']} @ {job['Company']} ---")
        print(f"  Location:  {job['Location']}")
        print(f"  Posted:    {job['Posted Date']}")
        print(f"  Level:     {job['Experience Level']}")
        print(f"  Skills:    {job['Skills']}")
        print(f"  Reqs:      {job['Requirements']}")
        print(f"  URL:       {job['URL']}")
