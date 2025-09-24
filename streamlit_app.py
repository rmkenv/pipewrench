import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional

# Configuration
API_BASE_URL = "http://localhost:8000/api"

class KnowledgeCaptureUI:
    def __init__(self):
        self.token = None
        if 'token' in st.session_state:
            self.token = st.session_state.token

    def make_api_request(self, endpoint: str, method: str = "GET", data: Any = None, files: Dict = None):
        """Make authenticated API request"""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"{API_BASE_URL}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                if files:
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    headers["Content-Type"] = "application/json"
                    response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                headers["Content-Type"] = "application/json"
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)

            if response.status_code == 401:
                st.session_state.token = None
                self.token = None
                st.error("Session expired. Please login again.")
                st.rerun()

            return response
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {e}")
            return None

    def login_page(self):
        """Login page"""
        st.title("🔐 Knowledge Capture MVP - Login")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")

                if submitted:
                    if username and password:
                        response = self.make_api_request(
                            "/auth/login",
                            method="POST",
                            data={"username": username, "password": password}
                        )

                        if response and response.status_code == 200:
                            token_data = response.json()
                            st.session_state.token = token_data["access_token"]
                            self.token = token_data["access_token"]
                            st.success("Logged in successfully!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.error("Please enter both username and password")

            st.markdown("---")

            # Registration form
            st.subheader("Register New Account")
            with st.form("register_form"):
                reg_username = st.text_input("Username", key="reg_username")
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                reg_full_name = st.text_input("Full Name", key="reg_full_name")
                reg_role = st.selectbox("Role", ["user", "manager", "admin"], key="reg_role")

                reg_submitted = st.form_submit_button("Register")

                if reg_submitted:
                    if all([reg_username, reg_email, reg_password]):
                        response = self.make_api_request(
                            "/auth/register",
                            method="POST",
                            data={
                                "username": reg_username,
                                "email": reg_email,
                                "password": reg_password,
                                "full_name": reg_full_name,
                                "role": reg_role
                            }
                        )

                        if response and response.status_code == 200:
                            st.success("Account created successfully! Please login.")
                        else:
                            st.error("Registration failed. Username or email may already exist.")
                    else:
                        st.error("Please fill in all required fields")

    def main_dashboard(self):
        """Main application dashboard"""
        st.set_page_config(
            page_title="Knowledge Capture MVP",
            page_icon="📚",
            layout="wide"
        )

        # Sidebar navigation
        with st.sidebar:
            st.title("📚 Knowledge Capture")

            # User info
            user_response = self.make_api_request("/auth/me")
            if user_response and user_response.status_code == 200:
                user_info = user_response.json()
                st.write(f"Welcome, {user_info['full_name'] or user_info['username']}!")
                st.write(f"Role: {user_info['role']}")

            st.markdown("---")

            # Navigation
            page = st.selectbox(
                "Navigate to:",
                [
                    "Dashboard",
                    "Document Management",
                    "Job Roles & Interviews",
                    "Knowledge Reports",
                    "Chat Assistant",
                    "Chat with Files",
                    "System Maintenance"
                ]
            )

            if st.button("Logout"):
                st.session_state.token = None
                st.rerun()

        # Main content area
        if page == "Dashboard":
            self.dashboard_page()
        elif page == "Document Management":
            self.document_management_page()
        elif page == "Job Roles & Interviews":
            self.job_roles_page()
        elif page == "Knowledge Reports":
            self.knowledge_reports_page()
        elif page == "Chat Assistant":
            self.chat_assistant_page()
        elif page == "Chat with Files":
            self.chat_files_page()
        elif page == "System Maintenance":
            self.maintenance_page()

    def dashboard_page(self):
        """Main dashboard with statistics"""
        st.title("📊 Knowledge Capture Dashboard")

        # Get statistics
        docs_response = self.make_api_request("/documents")
        reports_response = self.make_api_request("/knowledge-reports")

        if docs_response and reports_response:
            docs = docs_response.json()
            reports = reports_response.json()

            # Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Documents", len(docs))

            with col2:
                st.metric("Knowledge Reports", len(reports))

            with col3:
                completed_reports = len([r for r in reports if r['status'] == 'approved'])
                st.metric("Completed Reports", completed_reports)

            with col4:
                draft_reports = len([r for r in reports if r['status'] == 'draft'])
                st.metric("Draft Reports", draft_reports)

            # Charts
            col1, col2 = st.columns(2)

            with col1:
                # Document types chart
                if docs:
                    doc_types = {}
                    for doc in docs:
                        doc_type = doc.get('file_type', 'unknown')
                        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

                    fig = px.pie(
                        values=list(doc_types.values()),
                        names=list(doc_types.keys()),
                        title="Documents by Type"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Report status chart
                if reports:
                    status_counts = {}
                    for report in reports:
                        status = report.get('status', 'unknown')
                        status_counts[status] = status_counts.get(status, 0) + 1

                    fig = px.bar(
                        x=list(status_counts.keys()),
                        y=list(status_counts.values()),
                        title="Knowledge Reports by Status"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Recent activity
            st.subheader("Recent Knowledge Reports")
            if reports:
                recent_reports = sorted(reports, key=lambda x: x['created_at'], reverse=True)[:5]

                df = pd.DataFrame([
                    {
                        "Title": report['title'],
                        "Job Role": report['job_role'],
                        "Status": report['status'],
                        "Created": report['created_at'][:10]  # Just the date
                    }
                    for report in recent_reports
                ])

                st.dataframe(df, use_container_width=True)

    def document_management_page(self):
        """Document upload and management"""
        st.title("📄 Document Management")

        # Upload section
        st.subheader("Upload New Document")

        col1, col2 = st.columns(2)

        with col1:
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['txt', 'pdf', 'doc', 'docx'],
                help="Supported formats: TXT, PDF, DOC, DOCX"
            )

        with col2:
            document_type = st.selectbox(
                "Document Type",
                [
                    "job_description",
                    "sop",
                    "bmp",
                    "maintenance_plan",
                    "permit_requirement",
                    "org_chart",
                    "budget_tool",
                    "contractor_list",
                    "training_material",
                    "other"
                ]
            )

            document_category = st.text_input(
                "Category",
                placeholder="e.g., safety, operations, finance"
            )

        if st.button("Upload Document"):
            if uploaded_file and document_type:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {
                    "document_type": document_type,
                    "document_category": document_category or "general"
                }

                with st.spinner("Uploading and processing document..."):
                    response = self.make_api_request(
                        "/documents/upload",
                        method="POST",
                        data=data,
                        files=files
                    )

                    if response and response.status_code == 200:
                        result = response.json()
                        st.success(f"Document uploaded successfully! ID: {result['id']}")
                    else:
                        st.error("Failed to upload document")
            else:
                st.error("Please select a file and document type")

        st.markdown("---")

        # Document list
        st.subheader("Existing Documents")

        # Filter options
        col1, col2 = st.columns(2)

        with col1:
            filter_type = st.selectbox("Filter by Type", ["All"] + [
                "job_description", "sop", "bmp", "maintenance_plan",
                "permit_requirement", "org_chart", "budget_tool",
                "contractor_list", "training_material", "other"
            ])

        # Get documents
        endpoint = "/documents"
        if filter_type != "All":
            endpoint += f"?document_type={filter_type}"

        docs_response = self.make_api_request(endpoint)

        if docs_response and docs_response.status_code == 200:
            docs = docs_response.json()

            if docs:
                # Create DataFrame
                df = pd.DataFrame([
                    {
                        "ID": doc['id'],
                        "Filename": doc['filename'],
                        "Type": doc['file_type'],
                        "Category": doc['document_category'],
                        "Size (KB)": round(doc['file_size'] / 1024, 1) if doc['file_size'] else 0,
                        "Uploaded": doc['uploaded_at'][:10]
                    }
                    for doc in docs
                ])

                st.dataframe(df, use_container_width=True)

                # Document details
                if st.session_state.get('selected_doc_id'):
                    doc_id = st.session_state.selected_doc_id
                    doc_response = self.make_api_request(f"/documents/{doc_id}")

                    if doc_response and doc_response.status_code == 200:
                        doc_details = doc_response.json()

                        st.subheader(f"Document: {doc_details['filename']}")

                        col1, col2 = st.columns(2)

                        with col1:
                            st.write(f"**Type:** {doc_details['file_type']}")
                            st.write(f"**Category:** {doc_details['document_category']}")
                            st.write(f"**Uploaded:** {doc_details['uploaded_at']}")

                        with col2:
                            st.write(f"**Uploaded by:** {doc_details.get('uploaded_by', 'Unknown')}")

                        st.subheader("Content Preview")
                        if doc_details.get('content_text'):
                            st.text_area(
                                "Text Content",
                                doc_details['content_text'][:1000] + "..." if len(doc_details['content_text']) > 1000 else doc_details['content_text'],
                                height=200,
                                disabled=True
                            )

                # Select document for details
                selected_id = st.selectbox("View Document Details", [None] + [doc['id'] for doc in docs])
                if selected_id:
                    st.session_state.selected_doc_id = selected_id
                    st.rerun()
            else:
                st.info("No documents found")

    def job_roles_page(self):
        """Job roles and interview management"""
        st.title("👥 Job Roles & Interviews")

        tab1, tab2, tab3 = st.tabs(["Job Roles", "Generate Questions", "Interviews"])

        with tab1:
            st.subheader("Create New Job Role")

            with st.form("job_role_form"):
                title = st.text_input("Job Title")
                department = st.text_input("Department")
                description = st.text_area("Job Description")

                submitted = st.form_submit_button("Create Job Role")

                if submitted and title:
                    response = self.make_api_request(
                        "/job-roles",
                        method="POST",
                        data={
                            "title": title,
                            "department": department,
                            "description": description
                        }
                    )

                    if response and response.status_code == 200:
                        st.success("Job role created successfully!")
                        st.rerun()

            st.markdown("---")

            # List existing job roles
            st.subheader("Existing Job Roles")

            roles_response = self.make_api_request("/job-roles")

            if roles_response and roles_response.status_code == 200:
                roles = roles_response.json()

                if roles:
                    df = pd.DataFrame(roles)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No job roles found")

        with tab2:
            st.subheader("Generate Interview Questions")

            # Get job roles for selection
            roles_response = self.make_api_request("/job-roles")

            if roles_response and roles_response.status_code == 200:
                roles = roles_response.json()

                if roles:
                    role_options = {f"{role['title']} - {role['department'] or 'No Dept'}": role['id'] for role in roles}
                    selected_role = st.selectbox("Select Job Role", list(role_options.keys()))

                    if st.button("Generate Interview Questions"):
                        with st.spinner("Generating questions using AI..."):
                            role_id = role_options[selected_role]
                            response = self.make_api_request(
                                f"/interviews/generate-questions/{role_id}",
                                method="POST"
                            )

                            if response and response.status_code == 200:
                                questions = response.json()['questions']

                                st.success(f"Generated {len(questions)} questions!")

                                for i, question in enumerate(questions, 1):
                                    st.write(f"**{i}.** {question}")

                                # Store questions in session state for interview upload
                                st.session_state.generated_questions = questions
                                st.session_state.selected_role_id = role_id
                            else:
                                st.error("Failed to generate questions")
                else:
                    st.info("Please create job roles first")

        with tab3:
            st.subheader("Upload Interview Recording")

            if 'generated_questions' in st.session_state:
                audio_file = st.file_uploader(
                    "Upload Audio Recording",
                    type=['wav', 'mp3', 'mp4', 'm4a'],
                    help="Supported formats: WAV, MP3, MP4, M4A"
                )

                col1, col2 = st.columns(2)

                with col1:
                    # Get users for interviewee selection
                    # This would need a user list endpoint in the API
                    interviewee_id = st.number_input("Interviewee User ID", min_value=1, value=1)

                with col2:
                    interviewer_name = st.text_input("Interviewer Name")

                if st.button("Upload Interview"):
                    if audio_file and interviewer_name:
                        files = {"audio_file": (audio_file.name, audio_file.getvalue(), audio_file.type)}
                        data = {
                            "interviewee_id": interviewee_id,
                            "interviewer_name": interviewer_name,
                            "questions": json.dumps(st.session_state.generated_questions)
                        }

                        with st.spinner("Uploading interview and starting transcription..."):
                            response = self.make_api_request(
                                f"/interviews/upload-audio/{st.session_state.selected_role_id}",
                                method="POST",
                                data=data,
                                files=files
                            )

                            if response and response.status_code == 200:
                                result = response.json()
                                st.success(f"Interview uploaded! ID: {result['interview_id']}")
                                st.info("Transcription started in background. Check status later.")
                            else:
                                st.error("Failed to upload interview")
                    else:
                        st.error("Please upload audio file and enter interviewer name")
            else:
                st.info("Please generate questions first in the 'Generate Questions' tab")

    def knowledge_reports_page(self):
        """Knowledge reports management"""
        st.title("📋 Knowledge Reports")

        # List reports
        reports_response = self.make_api_request("/knowledge-reports")

        if reports_response and reports_response.status_code == 200:
            reports = reports_response.json()

            if reports:
                # Reports overview
                df = pd.DataFrame([
                    {
                        "ID": report['id'],
                        "Title": report['title'],
                        "Job Role": report['job_role'],
                        "Status": report['status'],
                        "Created": report['created_at'][:10],
                        "Updated": report['updated_at'][:10]
                    }
                    for report in reports
                ])

                st.dataframe(df, use_container_width=True)

                # Report details
                selected_report_id = st.selectbox("View Report Details", [None] + [report['id'] for report in reports])

                if selected_report_id:
                    report_response = self.make_api_request(f"/knowledge-reports/{selected_report_id}")

                    if report_response and report_response.status_code == 200:
                        report = report_response.json()

                        st.markdown("---")
                        st.subheader(f"📄 {report['title']}")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write(f"**Job Role:** {report['job_role']}")

                        with col2:
                            st.write(f"**Status:** {report['status']}")

                        with col3:
                            st.write(f"**Created:** {report['created_at'][:10]}")

                        # Report content
                        if report.get('content'):
                            st.subheader("Report Content")
                            st.markdown(report['content'])

                        # SWOT Analysis
                        if report.get('swot_analysis'):
                            st.subheader("SWOT Analysis")

                            swot = report['swot_analysis']

                            col1, col2 = st.columns(2)

                            with col1:
                                st.write("**Strengths:**")
                                for strength in swot.get('strengths', []):
                                    st.write(f"• {strength}")

                                st.write("**Opportunities:**")
                                for opp in swot.get('opportunities', []):
                                    st.write(f"• {opp}")

                            with col2:
                                st.write("**Weaknesses:**")
                                for weakness in swot.get('weaknesses', []):
                                    st.write(f"• {weakness}")

                                st.write("**Threats:**")
                                for threat in swot.get('threats', []):
                                    st.write(f"• {threat}")
            else:
                st.info("No knowledge reports found. Generate reports from completed interviews.")

    def chat_assistant_page(self):
        """Chat with knowledge base"""
        st.title("💬 Chat Assistant")

        st.write("Ask questions about organizational procedures, roles, and knowledge.")

        # Initialize chat history
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
            st.session_state.chat_session_id = None

        # Display chat history
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Show sources for assistant messages
                if message["role"] == "assistant" and message.get("sources"):
                    with st.expander("Sources"):
                        for source in message["sources"]:
                            st.write(f"📄 {source['source']}")
                            st.write(f"Relevance: {source['score']:.2f}")
                            st.write(f"Content: {source['content']}")
                            st.write("---")

        # Chat input
        if prompt := st.chat_input("Ask a question about organizational knowledge..."):
            # Add user message to chat history
            st.session_state.chat_messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = self.make_api_request(
                        "/chat/message",
                        method="POST",
                        data={
                            "message": prompt,
                            "session_id": st.session_state.chat_session_id
                        }
                    )

                    if response and response.status_code == 200:
                        result = response.json()

                        # Update session ID
                        st.session_state.chat_session_id = result["session_id"]

                        # Display response
                        st.markdown(result["response"])

                        # Add assistant message to chat history
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": result["response"],
                            "sources": result.get("sources", [])
                        })

                        # Show sources
                        if result.get("sources"):
                            with st.expander("Sources"):
                                for source in result["sources"]:
                                    st.write(f"📄 {source['source']}")
                                    st.write(f"Relevance: {source['score']:.2f}")
                                    st.write("---")
                    else:
                        st.error("Failed to get response from chat assistant")

        # Clear chat button
        if st.button("Clear Chat History"):
            st.session_state.chat_messages = []
            st.session_state.chat_session_id = None
            st.rerun()

    def chat_files_page(self):
        """Chat with uploaded files"""
        st.title("📁 Chat with Files")

        st.write("Upload a file and ask questions about its content.")

        # File upload
        uploaded_file = st.file_uploader(
            "Upload a file to chat with",
            type=['txt', 'pdf', 'doc', 'docx'],
            help="Upload a document to ask questions about its content"
        )

        if uploaded_file:
            if st.button("Process File for Chat"):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

                with st.spinner("Processing file..."):
                    response = self.make_api_request(
                        "/chat/upload-file",
                        method="POST",
                        files=files
                    )

                    if response and response.status_code == 200:
                        result = response.json()
                        st.session_state.chat_file_id = result["file_id"]
                        st.session_state.chat_file_name = result["filename"]
                        st.success(f"File '{result['filename']}' is ready for chat!")
                    else:
                        st.error("Failed to process file")

        # Chat interface for file
        if 'chat_file_id' in st.session_state:
            st.subheader(f"💬 Chat with: {st.session_state.chat_file_name}")

            # Initialize file chat history
            if 'file_chat_messages' not in st.session_state:
                st.session_state.file_chat_messages = []
                st.session_state.file_chat_session_id = None

            # Display chat history
            for message in st.session_state.file_chat_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Chat input
            if prompt := st.chat_input(f"Ask about {st.session_state.chat_file_name}..."):
                # Add user message
                st.session_state.file_chat_messages.append({"role": "user", "content": prompt})

                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing file..."):
                        response = self.make_api_request(
                            "/chat/message",
                            method="POST",
                            data={
                                "message": prompt,
                                "session_id": st.session_state.file_chat_session_id,
                                "file_id": st.session_state.chat_file_id
                            }
                        )

                        if response and response.status_code == 200:
                            result = response.json()

                            st.session_state.file_chat_session_id = result["session_id"]
                            st.markdown(result["response"])

                            st.session_state.file_chat_messages.append({
                                "role": "assistant",
                                "content": result["response"]
                            })
                        else:
                            st.error("Failed to get response")

            if st.button("Clear File Chat"):
                st.session_state.file_chat_messages = []
                st.session_state.file_chat_session_id = None
                st.rerun()

    def maintenance_page(self):
        """System maintenance interface"""
        st.title("🔧 System Maintenance")

        st.write("Manage system maintenance tasks and view system health.")

        # Maintenance tasks
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Run Maintenance Tasks")

            task_options = [
                "content_review",
                "reindex_vectors", 
                "cleanup_chat_sessions",
                "backup_database",
                "audit_user_access",
                "validate_transcriptions",
                "update_knowledge_reports"
            ]

            selected_task = st.selectbox("Select Task", task_options)

            if st.button(f"Run {selected_task}"):
                with st.spinner(f"Running {selected_task}..."):
                    response = self.make_api_request(
                        f"/maintenance/run-task/{selected_task}",
                        method="POST"
                    )

                    if response and response.status_code == 200:
                        st.success(f"Task '{selected_task}' started successfully!")
                    else:
                        st.error("Failed to run maintenance task")

        with col2:
            st.subheader("System Health")

            health_response = self.make_api_request("/health")

            if health_response and health_response.status_code == 200:
                health_data = health_response.json()
                st.success("✅ System is healthy")
                st.write(f"Status: {health_data['status']}")
                st.write(f"Last check: {health_data['timestamp']}")
            else:
                st.error("❌ System health check failed")

        st.markdown("---")

        # Maintenance history
        st.subheader("Maintenance History")

        history_response = self.make_api_request("/maintenance/history")

        if history_response and history_response.status_code == 200:
            history = history_response.json()

            if history:
                df = pd.DataFrame([
                    {
                        "Task": item['action_type'],
                        "Description": item['description'][:100] + "..." if len(item['description']) > 100 else item['description'],
                        "Status": item['status'],
                        "Date": item['performed_at'][:10]
                    }
                    for item in history
                ])

                st.dataframe(df, use_container_width=True)
            else:
                st.info("No maintenance history found")

    def run(self):
        """Main application runner"""
        if not self.token:
            self.login_page()
        else:
            self.main_dashboard()

# Run the application
if __name__ == "__main__":
    app = KnowledgeCaptureUI()
    app.run()
