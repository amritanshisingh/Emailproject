# Finance Credit Follow-Up Email Agent
# Task 2 - AI Enablement Internship
# Made by: [Your Name]
# LLM: Google Gemini (Free)

import os
import csv
import json
import time
from datetime import datetime, date
import google.generativeai as genai
from dotenv import load_dotenv

# load the API key from .env file
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-flash-latest")


# sanitise function to strip potentially harmful characters for prompt injection mitigation
def sanitise(text):
    if not isinstance(text, str):
        text = str(text)
    return text.replace("{", "").replace("}", "").replace("`", "")


# this function figures out which stage/tone to use based on how many days overdue
def get_stage(days_overdue):
    if days_overdue <= 7:
        return 1   # friendly reminder
    elif days_overdue <= 14:
        return 2   # polite but firm
    elif days_overdue <= 21:
        return 3   # formal and serious
    elif days_overdue <= 30:
        return 4   # stern and urgent
    else:
        return 5   # legal escalation - no email, just flag it


# this function calls Gemini API and generates the email based on the stage
def generate_email(client_name, invoice_no, amount, due_date, days_overdue, contact_email, stage):

    # decide the tone based on stage number
    if stage == 1:
        tone = "warm and friendly. Write like you are doing a gentle favour reminder."
    elif stage == 2:
        tone = "polite but firm. Payment is still pending, ask them to confirm a date."
    elif stage == 3:
        tone = "formal and serious. Mention this is escalating and they must respond in 48 hours."
    elif stage == 4:
        tone = "stern and urgent. This is the final reminder before legal action."

    prompt = f"""
Write a payment follow-up email with a {tone} tone.

Use these details:
- Client Name: {sanitise(client_name)}
- Invoice Number: {sanitise(invoice_no)}
- Amount Due: Rs. {sanitise(amount)}
- Due Date: {sanitise(due_date)}
- Days Overdue: {days_overdue}
- Payment Link: https://pay.example.com/{sanitise(invoice_no)}

Important rules:
- Use first name only for stage 1, use Mr./Ms. with last name for stage 3 and 4
- Always mention the invoice number and amount
- Keep it under 120 words
- End with a clear call to action

Return ONLY a JSON object with two keys: "subject" and "body"
Do not add any extra text or markdown, just the JSON.
"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # sometimes Gemini adds ```json at the start, so remove that
        if result_text.startswith("```"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()

        email_data = json.loads(result_text)
        return email_data

    except json.JSONDecodeError as e:
        print(f"  ERROR: Gemini returned something that is not valid JSON - {e}")
        return None

    except Exception as e:
        print(f"  ERROR: Something went wrong while calling the Gemini API - {e}")
        return None


# main function that reads the CSV and processes all invoices
def run_agent():

    # create folders if they don't exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    today = date.today()
    all_results = []
    audit_log = []

    print("\n--- Finance Follow-Up Email Agent Starting ---\n")

    # read the invoices CSV file
    try:
        with open("data/invoices.csv", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            invoices = list(reader)
        print(f"Found {len(invoices)} invoices in the CSV file\n")
    except FileNotFoundError:
        print("ERROR: invoices.csv file not found. Please make sure it is inside the data/ folder.")
        return []

    for invoice in invoices:

        # calculate how many days overdue this invoice is
        try:
            due_date = datetime.strptime(invoice["due_date"], "%d-%m-%Y").date()
            days_overdue = (today - due_date).days
        except ValueError:
            print(f"SKIP: {invoice['invoice_no']} - due_date format is wrong, expected DD-MM-YYYY")
            continue

        # skip invoices that are not due yet
        if days_overdue <= 0:
            print(f"SKIP: {invoice['invoice_no']} - not due yet (due on {invoice['due_date']})")
            continue

        stage = get_stage(days_overdue)

        # if overdue more than 30 days, flag it for legal team instead of sending email
        if stage == 5:
            print(f"LEGAL FLAG: {invoice['invoice_no']} - {days_overdue} days overdue - needs human review")

            audit_log.append({
                "time": str(datetime.now()),
                "invoice_no": invoice["invoice_no"],
                "client": invoice["client_name"],
                "days_overdue": days_overdue,
                "stage": "LEGAL",
                "subject": "No email - flagged for legal",
                "status": "FLAGGED"
            })

            all_results.append({
                "invoice": invoice["invoice_no"],
                "client": invoice["client_name"],
                "days_overdue": days_overdue,
                "stage": "LEGAL FLAG",
                "status": "Needs human review - no email sent"
            })
            continue

        print(f"Processing: {invoice['invoice_no']} | {invoice['client_name']} | {days_overdue} days overdue | Stage {stage}")

        # call Gemini to generate the email
        email = generate_email(
            client_name=invoice["client_name"],
            invoice_no=invoice["invoice_no"],
            amount=invoice["amount"],
            due_date=invoice["due_date"],
            days_overdue=days_overdue,
            contact_email=invoice["contact_email"],
            stage=stage
        )

        # if email generation failed, skip this invoice and move to the next one
        if email is None:
            print(f"  SKIPPING {invoice['invoice_no']} because email could not be generated\n")
            print("  Waiting 15 seconds to respect API rate limits...")
            time.sleep(15)
            continue

        print(f"  Subject: {email['subject']}")
        print(f"  Status: DRY RUN (email not actually sent)\n")

        # save to audit log
        audit_log.append({
            "time": str(datetime.now()),
            "invoice_no": invoice["invoice_no"],
            "client": invoice["client_name"],
            "days_overdue": days_overdue,
            "stage": stage,
            "subject": email["subject"],
            "status": "DRY_RUN"
        })

        # save the full email to results
        all_results.append({
            "invoice": invoice["invoice_no"],
            "client": invoice["client_name"],
            "days_overdue": days_overdue,
            "stage": stage,
            "subject": email["subject"],
            "body": email["body"],
            "status": "DRY_RUN"
        })

        # Sleep to avoid hitting free-tier API rate limits
        print("  Waiting 15 seconds to respect API rate limits...")
        time.sleep(15)

    # save audit log to file
    try:
        with open("logs/audit_log.json", "w") as f:
            json.dump(audit_log, f, indent=2)
        print("Audit log saved to: logs/audit_log.json")
    except Exception as e:
        print(f"ERROR: Could not save audit log - {e}")

    # save all generated emails to file
    try:
        with open("output/emails_output.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print("All emails saved to: output/emails_output.json")
    except Exception as e:
        print(f"ERROR: Could not save emails output file - {e}")

    print(f"\n--- Done! ---")
    print(f"Total processed: {len(all_results)}\n")

    return all_results


# run the agent when this file is executed
if __name__ == "__main__":
    run_agent()