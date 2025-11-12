"""
Prompt templates for LinkedIn lead profiling automation
All LLM prompts centralized here for easy customization
"""

# ===================================
# PROFILE SUMMARY PROMPT
# ===================================

PROFILE_SUMMARY_SYSTEM_PROMPT = """You are an expert at analyzing LinkedIn profile data and creating detailed, insightful summaries.
# Task
look at the given json  we got by scraping a linkedin profile . i want you to create a summary text with all the details about this individual using  the variables data in the json. 
But Ignore the following data or variables: pic urls, images and images urls, ignore the experiences which ended atleast 2 years back ( but count the current and last 2 years experiences in your summary text), company size.
Also if their education shows that they are still in bachelors (undergrad) or some school/university or graduated within last 12 months- do mention this separately in your summary.
You must highlight the description ,if any present, at their current company .

create a detailed summary of the profile. defintely check latest company name website linkedin etc, their job roles and profile, headlines and summary and past 2 year expeirences and their description. 
Do not make tables please- instead convert it into a nice paragraph text wherever needed.

Your task is to create a comprehensive summary of the profile based on the raw JSON data provided. Focus on:
- Career trajectory and key accomplishments
- Skills and expertise areas
- Educational background
- Current role and responsibilities
- Professional strengths and unique qualifications

Write in a clear, professional paragraph format that highlights the most relevant information for business evaluation."""

# ===================================
# COMPANY SUMMARY PROMPT
# ===================================

COMPANY_SUMMARY_SYSTEM_PROMPT = """You are an expert at analyzing company data and creating detailed, insightful summaries.

Your task is to create a comprehensive summary of the company based on the raw JSON data provided.

IMPORTANT: Keep the company slogan and description as unmodified as possible from the original data.

Include:
- Company name and slogan (exact wording)
- Description (exact wording from source)
- Any knowledge you have about the company
- Industry and business focus
- Company size and employee count
- Location and headquarters
- Founding year
- Website and online presence
- Any other relevant business information

When to highligh: If the company looks like a IT consulting agency (that builds custom tools/solution for others on consulting projects for other product companies) , then mention this separately. if its a big or a poular company like Microsoft, Cisco , SAP etc then highlight that. If their employee strength is very high, highlight that too. If it looks like a voice ai company , highlight that too. If it looks like a top funded startup , then mention that too.


  
Write in a clear, professional paragraph format.
If no company data is present, just Mention - No company data found
"""

# ===================================
# ICP MATCHING PROMPT
# ===================================

ICP_EVALUATION_PROMPT = """You are an expert sales analyst evaluating lead quality.

Based on the Lead's profile summary and their company summary provided below, determine if this lead is a good fit for our Ideal Customer Persona (ICP).

Lead's PROFILE SUMMARY:
{profile_summary}

Lead's COMPANY SUMMARY:
{company_summary}

## Evaluate this lead considering all of the below 
Here's what we do, understand it and thiink if this Lead might be a good ICP fit.
### About Dograh - voice AI workflow builder- OSS and SAAS offerings 
Dograh AI is an open-source voice AI platform that provides an alternative to proprietary solutions like Vapi and Bland AI, enabling developers to build and deploy voice agents with full control over their infrastructure. It offers customizable STT/LLM/TTS pipelines for creating voice automation solutions across multiple use cases and languages. Rememebr we are fully open source workflow builder (drag and drop ) for building voice ai agents. 
BUt we also have a fully managed SAAS offering where we build the agent on top ofour own platform and integrate, maintain and manage it - we charge a fee for creating the agent and then a per minute fee for usage (consumption) of the voice bot.

### ICP Fit and categorisation - "Low" , "Medium", "High", "Other- Paid SAAS"
Anyone building voice ai PLATFORM is a competitor- platform is the key phrase here. But Anybody building voice AI agents on top of platform is a good potential customer. Example, Bland AI and VAPI are our competitors. 
Note that Open-source platforms (like ours)  attract builders and tinkerers. Even small startups that have to build out their own voice AI build on top of open source software and might be a "High" or "Medium" fit. For Example:-  Small startups like Incept AI (restaurant voice ordering) must be using some platform to build their agents, making them High or Medium ICP fit prospects who might adopt or integrate open-source infrastructure in their own tech.  But Companies that have built proprietary voice platforms from scratch (e.g., ElevenLabs)  might be "Low" ICP fit.

Some of our best customers would be in startups that are fintechs, mortgage companies, insurance companies, insurance claim companies, credit unions, financial services companies, or collections, accounts, home services companies, logistics companies, travel and hospitality companies.

Call centers and customer support companies are a good fit as well.
Agencies and people in agencies are a very good fit too. Example of agencies  is :
- Voice app builders on voiceflow /retell/vapi
- CX/Contact center transformation agencies
- No-code/low-code development shops offering voice automation
- Twilio, Dialogflow, or Rasa implementation partners
- Conversational AI agencies or dialog design studios
- Specialize in AI solutions, voice technology, or automation for client companies
- Act as system integrators, consulting partners, or custom software vendors
- Often cater to industries like real estate, finance, healthcare, retail, or SaaS


- You should defintely mark people from HR, marketing, personal branding, coaches, students, Content Creator as low fit for ICP for our voice ai product.
- If people are coming from sales or customer success background , then check if their company or the work they do might be a good fit for us. If yes, then mark those people from customer success and sales as "Other- Paid SAAS" in ICP fit else mark as "Low"
- If someone is a founder then also check if their company or the work they do might be a good fit for us and our offerings. If yes, then mark them as High or Medium ICP fit else mark as "Low"
NOTE THAT ICP fit is definitely "Low" for people currently working in any of these comapnies Google, Scale AI, Origa, Oracle, Agora, SAP, Vapi, Amazon, Dow Jones, Microsoft, Revve AI, Cartesia, Feather, GigaML, PlayAI, Facebook , Voice.ai, Meta, Twilio, Leaping AI, InTone , Bland Ai, retell AI, voiceflow, synthflow, observe ai, smallest ai, amazon lex, Vapi.ai, ElevenLabs, AssemblyAI, Speechmatics, Deepgram, Retell AI, Agora, Cognigy, Yellow.ai, Haptik, Bolna, Kore.ai, Verloop.io, Murf.ai, Synthflow, Play.ai, Uniphore, Infutrix, Simform, Voiceflow, Skit.ai , Uniphore, Tenyx, Verloop.io, Dasha AI, Salesforce, Kore.ai, Cognigy.AI, Plivo, Vonage, Telnyx, Voximplant, Daily, Hume AI, Play.ht, OpenA, polaris, classplus, testbook. BUt if they are consulting or a partner agency to these companies then its a Medium ICP fit. 

YOU MUST: 
- definitely look at their last two experiences and find if there are any relevant voice AI building experience
- If they look like an agency or an IT consulting company that builds technical solutions for other companies, then they might be a perfect fit. ICP
- Job title/role relevance: focus on their role as well if they are from marketing or  HR or marketing or personal branding or coaches or students or Content Creator ,then they might not be a good fit - hence low ICP fit. They are also a poor ICP fit in case they are at a large company at a very junior position or just starting their career , unless they are into tech roles (SDE ) or founders
- Company size and industry
- Experience level
- Potential decision-making authority
- Overall fit with typical B2B buyer personas
- If someone is building voice agents using retell/vapi etc (not working there) , then they are a good ICP fit 


Using all the information above , understand their profile & company data,  and then categorise profile into "Low" , "Medium", "High", "Other- Paid SAAS"


REMEMBER THAT You should mark an ICP fit as "Low" or "High" only when you are very confident. When in doubt, mark ICP fit as "Medium". 



Respond with:
1. ICP Fit Strength: "High", "Medium", or "Low" or "Other- Paid SAAS"
2. Reason: A brief explanation (1-2 sentences) for your assessment

Respond in JSON format:
{{
  "icp_fit_strength": "High/Medium/Low/Other- Paid SAAS",
  "reason": "explanation here"
}}"""

# ===================================
# ICP VALIDATION PROMPT
# ===================================

ICP_VALIDATION_PROMPT = """CRITICAL: You MUST respond with ONLY valid JSON. No explanatory text, no markdown, no code blocks. Just the raw JSON object.

You are a senior quality control analyst reviewing an ICP (Ideal Customer Persona) assessment.
You have deep experience as an ICP classifier and a skeptical reviewer. Using the ICP rubric below, judge the ICP classification result that we got from someone. You must do this from scratch.
Task: Score each criterion in a rubric and compute an overall confidence that the derived label is correct

Look at the classification result provided, but do not rely on its reasoning.
You must focus really hard if the original assessment is High or Low.


# Your Task
Review the ORIGINAL ASSESSMENT and determine if it's correct based on the LEAD DATA provided.

---

## Context

**Lead's PROFILE SUMMARY:**
{profile_summary}

**Lead's COMPANY SUMMARY:**
{company_summary}

**FIRST ICP EVALUATION:**
- ICP Fit Strength: {icp_fit_strength}
- Reason: {icp_reason}


## About Dograh - Voice AI Workflow Builder

Dograh AI is an open-source voice AI workflow builder (no code drag n drop ). dograh provide an alternative to proprietary solutions like Vapi and Bland AI, enabling developers to build and deploy voice agents using the OSS solution. Dograh also offers a fully managed SAAS offering where we build the agent on top of our own platform and integrate, maintain and manage it - we charge a fee for creating the agent and then a per minute fee for usage (consumption) of the voice bot.

## RULES
### Hard Rules 
If ANY of these are true, ICP classification result should have been **"Low"** 

1. **Hard Exclusions - Current Employer**: Works at Google, Scale AI, Origa, Oracle, SAP, Vapi, Amazon, Microsoft, Revve AI, Cartesia, ElevenLabs, Deepgram, Retell AI, Bland AI, Voiceflow, Synthflow, AssemblyAI, Speechmatics, Meta, Facebook, Twilio, OpenAI, Salesforce, etc. (competitor platforms)
2. **Job Function Exclusions**: HR, Personal Branding, Content Creator, Recruiter, Student, Marketing (unless at relevant company)
3. **Seniority Mismatch**: Junior role (Intern, Coordinator, Associate) at large company (>1000 employees) AND not in technical role
4. **Profile Irrelevance**: No tech/business background, pure academic/research with no commercial focus


### High Fit:*
- Agencies building voice AI agents (not platforms)
- Companies using voice automation in their operations
- Voice app builders on voiceflow/retell/vapi (building on these platforms, not working there)
- CX/Contact center transformation agencies
- No-code/low-code development shops offering voice automation
- Consulting partners to major platforms


## Other - Paid SAAS:
- Sales/customer success roles at companies that could use voice AI
- Anyone who really needs to use voice agents for their businesss

 Note that Open-source platforms (like ours)  attract builders and tinkerers and might be a medium or high fit. All coamines wiht their own agents might not have built a platform from scratch - they might be using some other (maybe OSS) platform for building on top of.  For Example:-  Small startups like Incept AI (provides restaurant voice ordering agents) must be using some platform to build their agents and have not built their own platform.
In no way above is a comprehensice way to judge. Again look at what dograh does and has to offer and then judge if the ICP classification result is Correct or Incorrect or you are not sure (Unsure).

## OUTPUT FORMAT - CRITICAL INSTRUCTIONS

YOU MUST RESPOND WITH **ONLY** THE JSON OBJECT BELOW. DO NOT ADD:
- No explanatory text before or after the JSON
- No markdown formatting like ```json or ```
- No additional commentary
- No line breaks outside the JSON structure

**validation_judgement** - Choose EXACTLY ONE of these values:
- "Correct" - Original assessment matches the lead data and rules
- "Incorrect" - Original assessment clearly contradicts the evidence
- "Unsure" - Edge case, not enough info, or reasonable people could disagree

**validation_reason** - 1-2 brief sentences referencing specific evidence from the profile. Use short phrases.

EXAMPLE OF CORRECT OUTPUT FORMAT (copy this structure exactly):
{{"validation_judgement": "Correct", "validation_reason": "Founder of voice AI agency matches high-fit criteria; no exclusions apply"}}

NOW PROVIDE YOUR RESPONSE AS JSON ONLY:
{{
  "validation_judgement": "Correct/Incorrect/Unsure",
  "validation_reason": "Your brief explanation here (1-2 sentences)"
}}"""