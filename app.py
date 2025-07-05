"""
Streamlit RAG Chatbot with Message Logs (Enhanced UI - Pure Streamlit)
--------------------------------------------------------------------
• Upload one or multiple files (PDF, PPTX, DOCX, CSV, TXT)
• Ask multi‑turn questions about the uploaded corpus
• Sidebar has two tabs: **Upload** and **Logs**
• All MCP messages are captured and displayed in Logs
• Enhanced UI using only Streamlit components

Run with:
    streamlit run app.py
"""

import os
import uuid
import json
import time
from pathlib import Path
from typing import List
import streamlit as st

# ---- internal imports ----
from project.mcp.messageBus import MessageBus
from project.agents.coordinatorAgent import CoordinatorAgent
from project.agents.ingestionAgent import IngestionAgent
from project.agents.retrievalAgent import RetrievalAgent
from project.agents.llmResponseAgent import LLMResponseAgent
from dotenv import load_dotenv
load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY")
# ------------------------------------------------------------
# 1. Initialize singletons once per Streamlit session
# ------------------------------------------------------------
if "bus" not in st.session_state:
    bus = MessageBus()
    st.session_state.bus = bus
    st.session_state.logs = []
    st.session_state.show_logs_json = False
    st.session_state.upload_status = None
    st.session_state.processing_files = False

    # log wrapper
    def _logging_send(msg: dict):
        st.session_state.logs.append(msg)
        MessageBus.send(bus, msg)  # call original unbound send

    bus.send = _logging_send  # type: ignore

    # create agents
    st.session_state.coordinator = CoordinatorAgent(bus)
    st.session_state.ingestion   = IngestionAgent(bus)
    st.session_state.retrieval   = RetrievalAgent(bus)
    st.session_state.llm_agent   = LLMResponseAgent(bus, google_api_key=google_api_key)

    st.session_state.chat_history = []

bus = st.session_state.bus

# ------------------------------------------------------------
# 2. Sidebar (Upload & Logs)
# ------------------------------------------------------------
with st.sidebar:
    tab_upload, tab_logs = st.tabs(["⬆️ Upload", "📜 Logs"])

    with tab_upload:
        st.header("📁 Upload Documents")
        st.caption("Supported: PDF, PPTX, DOCX, CSV, TXT, MD")
        
        uploaded_files = st.file_uploader(
            "Choose file(s)", 
            accept_multiple_files=True,
            type=["pdf", "pptx", "csv", "docx", "txt", "md"],
            help="Select one or more files to add to your knowledge base"
        )
        
        # Show file count if files are selected
        if uploaded_files:
            st.info(f"📄 {len(uploaded_files)} file(s) selected")
        
        # Upload button with status
        if st.session_state.processing_files:
            st.warning("⏳ Processing files... Please wait")
            upload_disabled = True
        else:
            upload_disabled = not uploaded_files
        
        if st.button("🚀 Add to Knowledge Base", disabled=upload_disabled, use_container_width=True):
            st.session_state.processing_files = True
            st.rerun()
        
        # Handle file upload
        if st.session_state.processing_files and uploaded_files:
            try:
                temp_dir = Path("tmp_uploads")
                temp_dir.mkdir(exist_ok=True)
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_placeholder = st.empty()
                
                for i, file in enumerate(uploaded_files):
                    status_placeholder.text(f"Processing: {file.name}")
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    
                    file_path = temp_dir / file.name
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    
                    # Send to IngestionAgent
                    bus.send({
                        "sender":   "UI",
                        "receiver": "IngestionAgent",
                        "type":     "QUERY",
                        "trace_id": str(uuid.uuid4()),
                        "payload":  {"doc_path": str(file_path)},
                    })
                
                # Success message
                st.success(f"✅ Successfully uploaded {len(uploaded_files)} file(s)!")
                st.session_state.processing_files = False
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error uploading files: {str(e)}")
                st.session_state.processing_files = False

    with tab_logs:
        st.header("📊 Message Logs")
        
        # Log statistics
        total_logs = len(st.session_state.logs)
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Messages", total_logs)
        
        with col2:
            if total_logs > 0:
                recent_msg = st.session_state.logs[-1]
                st.metric("Latest", recent_msg.get('type', 'Unknown'))
        
        # Control buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Toggle JSON", help="Show/hide JSON logs"):
                st.session_state.show_logs_json = not st.session_state.show_logs_json
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear All", help="Clear all logs"):
                st.session_state.logs = []
                st.session_state.show_logs_json = False
                st.rerun()
        
        # Show JSON if toggled
        if st.session_state.show_logs_json and st.session_state.logs:
            st.subheader("JSON Export")
            logs_json = json.dumps(st.session_state.logs, indent=2)
            st.code(logs_json, language="json")
            
            # Download button
            st.download_button(
                label="💾 Download JSON",
                data=logs_json,
                file_name="mcp_logs.json",
                mime="application/json"
            )
        
        # Recent message list
        if st.session_state.logs:
            st.subheader("Recent Messages")
            
            # Filter options
            message_types = list(set(msg.get('type', 'Unknown') for msg in st.session_state.logs))
            selected_types = st.multiselect(
                "Filter by type:",
                message_types,
                default=message_types,
                help="Select message types to display"
            )
            
            # Display filtered logs
            filtered_logs = [msg for msg in st.session_state.logs if msg.get('type') in selected_types]
            display_logs = list(reversed(filtered_logs[-20:]))  # Last 20 messages
            
            for i, msg in enumerate(display_logs):
                msg_type = msg.get('type', 'Unknown')
                sender = msg.get('sender', 'Unknown')
                receiver = msg.get('receiver', 'Unknown')
                
                # Choose emoji based on message type
                emoji_map = {
                    "USER_QUERY": "🙋‍♂️",
                    "LLM_RESPONSE": "🤖",
                    "QUERY": "🔍",
                    "RESPONSE": "💬",
                    "ERROR": "❌",
                    "SUCCESS": "✅"
                }
                emoji = emoji_map.get(msg_type, "📨")
                
                with st.expander(f"{emoji} {msg_type}: {sender} → {receiver}"):
                    st.json(msg)

# ------------------------------------------------------------
# 3. Main Chat Interface
# ------------------------------------------------------------
st.title("📄🧠 Agentic RAG Chatbot")
st.caption("Ask questions about your uploaded documents")

# Show welcome message if no chat history
if not st.session_state.chat_history:
    st.info("👋 Welcome! Upload some documents using the sidebar and start asking questions.")

# Display chat history
for i, (user_msg, assistant_msg) in enumerate(st.session_state.chat_history):
    # User message
    with st.chat_message("user"):
        st.write(user_msg)
    
    # Assistant message
    with st.chat_message("assistant"):
        if assistant_msg == "(thinking…)":
            with st.spinner("🤔 Processing your question..."):
                st.write("Thinking...")
        else:
            st.write(assistant_msg)

# Chat input
user_input = st.chat_input("Ask a question about your documents...")

if user_input:
    st.session_state.chat_history.append((user_input, "(thinking…)"))
    st.rerun()

# ------------------------------------------------------------
# 4. Process pending user query
# ------------------------------------------------------------
if st.session_state.chat_history and st.session_state.chat_history[-1][1] == "(thinking…)":
    query = st.session_state.chat_history[-1][0]
    
    # Send query only once
    if "waiting_for_response" not in st.session_state:
        trace_id = str(uuid.uuid4())
        st.session_state.waiting_trace_id = trace_id
        st.session_state.waiting_for_response = True
        st.session_state.initial_log_count = len(st.session_state.logs)
        
        bus.send({
            "sender":   "UI",
            "receiver": "CoordinatorAgent",
            "type":     "USER_QUERY",
            "trace_id": trace_id,
            "payload":  {"query": query},
        })

    # Check for new LLM_RESPONSE
    if "initial_log_count" in st.session_state:
        current_log_count = len(st.session_state.logs)
        if current_log_count > st.session_state.initial_log_count:
            # Look for LLM_RESPONSE in new logs
            for msg in st.session_state.logs[st.session_state.initial_log_count:]:
                if msg.get("type") == "LLM_RESPONSE" and "payload" in msg and "answer" in msg["payload"]:
                    # Found response!
                    answer = msg["payload"]["answer"]
                    st.session_state.chat_history[-1] = (query, answer)
                    del st.session_state.waiting_for_response
                    del st.session_state.waiting_trace_id
                    del st.session_state.initial_log_count
                    st.rerun()
                    break
    
    # Continue waiting
    time.sleep(0.2)
    st.rerun()

# ------------------------------------------------------------
# 5. Footer with stats
# ------------------------------------------------------------
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Messages", len(st.session_state.logs))

with col2:
    st.metric("Conversations", len(st.session_state.chat_history))

with col3:
    if st.session_state.logs:
        active_agents = len(set(msg.get('sender', 'Unknown') for msg in st.session_state.logs))
        st.metric("Active Agents", active_agents)
    else:
        st.metric("Active Agents", 0)