import os
from Pdf_Utils import extract_text_from_pdf
from Github_Utils import summarize_text, ask_question_about_text

def main():
    print("=== PDF Chatbot ===")

    # Ask user to specify PDF file path
    pdf_path = input("Please enter the path to the PDF file: ").strip()
    if not os.path.isfile(pdf_path):
        print(f"Error: The file '{pdf_path}' does not exist.")
        return

    # Extract text from PDF
    print("\nExtracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        print("No text found in the PDF.")
        return

    # Summarize the text
    print("\nSummary of the PDF:")
    try:
        summary = summarize_text(text)
        print(summary)
    except Exception as e:
        print(f"Error with GitHub API: {e}")
        return

    # Ask questions about the text
    while True:
        print("\nYou can now ask questions about the document!")
        question = input("Enter your question (or type 'exit' to quit): ").strip()
        if question.lower() == "exit":
            print("Exiting the chatbot. Goodbye!")
            break
        try:
            answer = ask_question_about_text(text, question)
            print("\nAnswer:")
            print(answer)
        except Exception as e:
            print(f"Error with GitHub API: {e}")
            break

if __name__ == "__main__":
    main()