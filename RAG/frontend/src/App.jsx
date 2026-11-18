// Import React and the useState hook for managing UI state
import React, { useState } from "react";

// Define the base URL where the FastAPI backend is running
const API_BASE = "http://localhost:8000";

// Export the main React component
export default function App() {
  // State to store the selected PDF file object
  const [file, setFile] = useState(null);
  // State to store status messages during file upload
  const [uploadStatus, setUploadStatus] = useState("");
  // State to store the current text typed in the question box
  const [question, setQuestion] = useState("");
  // State array to hold the chat message history
  const [chatHistory, setChatHistory] = useState([]);
  // State boolean to show a loading indicator while waiting for the API
  const [loading, setLoading] = useState(false);

  // Define async handler for uploading the selected PDF
  const handleUpload = async (e) => {
    // Prevent default browser form submission reload
    e.preventDefault();
    // Stop execution if no file has been chosen
    if (!file) return;

    // Create a FormData instance to send binary file data
    const formData = new FormData();
    // Append the file under the key 'file' matching FastAPI's parameter name
    formData.append("file", file);
    // Display indexing progress message to the user
    setUploadStatus("Indexing document...");

    try {
      // Send a POST request with the PDF file to '/upload'
      const res = await fetch(`${API_BASE}/upload`, {
        // Specify HTTP POST method
        method: "POST",
        // Attach the multipart FormData body
        body: formData,
      });
      // Parse the JSON response from FastAPI
      const data = await res.json();
      // Set success message if HTTP status is 200-299, otherwise show error detail
      setUploadStatus(res.ok ? data.message : data.detail);
    } catch (err) {
      // Handle network failures when backend is unreachable
      setUploadStatus("Upload failed. Check backend server.");
    }
  };

  // Define async handler for submitting a chat question
  const handleAsk = async (e) => {
    // Prevent default page reload
    e.preventDefault();
    // Do not submit empty or whitespace-only questions
    if (!question.trim()) return;

    // Create a user message object
    const userMsg = { role: "user", text: question };
    // Append the user message immediately to the chat history UI
    setChatHistory((prev) => [...prev, userMsg]);
    // Clear the text input box
    setQuestion("");
    // Set loading state to true
    setLoading(true);

    try {
      // Send POST request with the question JSON to '/chat'
      const res = await fetch(`${API_BASE}/chat`, {
        // Specify HTTP POST method
        method: "POST",
        // Tell the server we are sending JSON data
        headers: { "Content-Type": "application/json" },
        // Stringify the question object
        body: JSON.stringify({ question: userMsg.text }),
      });
      // Parse the JSON response containing answer and sources
      const data = await res.json();
      // Append the AI's reply and source citations to chat history
      setChatHistory((prev) => [
        ...prev,
        { role: "ai", text: data.answer, sources: data.sources },
      ]);
    } catch (err) {
      // Append an error message to chat history on network failure
      setChatHistory((prev) => [
        ...prev,
        { role: "ai", text: "Error connecting to AI service." },
      ]);
    } finally {
      // Reset loading state to false once request finishes
      setLoading(false);
    }
  };

  // Render the component UI
  return (
    // Main centered container div
    <div style={{ maxWidth: "700px", margin: "40px auto", fontFamily: "sans-serif" }}>
      {/* Application Title */}
      <h2>DocuChat: Full-Stack RAG Assistant</h2>

      {/* PDF Upload Form */}
      <form onSubmit={handleUpload} style={{ marginBottom: "24px", padding: "16px", border: "1px solid #ccc" }}>
        {/* Section Heading */}
        <h4>1. Upload Knowledge Base (PDF)</h4>
        {/* File input restricted to .pdf files */}
        <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />
        {/* Submit button for upload */}
        <button type="submit" style={{ marginLeft: "10px" }}>Upload & Index</button>
        {/* Conditionally render upload status message */}
        {uploadStatus && <p style={{ color: "green", marginTop: "8px" }}>{uploadStatus}</p>}
      </form>

      {/* Chat History Display Box */}
      <div style={{ border: "1px solid #ccc", padding: "16px", minHeight: "300px", marginBottom: "16px" }}>
        {/* Loop through chatHistory array and render each message */}
        {chatHistory.map((msg, idx) => (
          // Message wrapper div with unique key
          <div key={idx} style={{ marginBottom: "12px" }}>
            {/* Bold sender label */}
            <strong>{msg.role === "user" ? "You: " : "AI: "}</strong>
            {/* Message text content */}
            <span>{msg.text}</span>
            {/* Conditionally render source citations if present */}
            {msg.sources && msg.sources.length > 0 && (
              // Citation footer div
              <div style={{ fontSize: "12px", color: "#555", marginTop: "4px" }}>
                Sources: {msg.sources.map((s) => `${s.source} (Chunk ${s.chunk_index})`).join(", ")}
              </div>
            )}
          </div>
        ))}
        {/* Show loading text while waiting for AI response */}
        {loading && <p>Thinking...</p>}
      </div>

      {/* Question Input Form */}
      <form onSubmit={handleAsk} style={{ display: "flex", gap: "8px" }}>
        {/* Controlled text input bound to question state */}
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your uploaded PDF..."
          style={{ flex: 1, padding: "8px" }}
        />
        {/* Submit button disabled while loading */}
        <button type="submit" disabled={loading}>Send</button>
      </form>
    </div>
  );
}
