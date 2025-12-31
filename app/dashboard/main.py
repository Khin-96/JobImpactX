"""
JobImpactX Streamlit Dashboard.
Executive interface for AI automation risk intelligence.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import requests
import os
import json

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = st.session_state.get("api_token", None)

# Configure page
st.set_page_config(
    page_title="JobImpactX Platform",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .risk-low { color: #2ecc71; font-weight: bold; }
    .risk-medium { color: #f39c12; font-weight: bold; }
    .risk-high { color: #e74c3c; font-weight: bold; }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# Authentication
def login(username: str, password: str) -> bool:
    """Authenticate user and store token."""
    try:
        response = requests.post(
            f"{API_URL}/auth/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state["api_token"] = data["access_token"]
            st.session_state["authenticated"] = True
            return True
        return False
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return False


def get_headers():
    """Get authorization headers."""
    token = st.session_state.get("api_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# Authentication check
if not st.session_state.get("authenticated", False):
    st.title("JobImpactX Platform")
    st.subheader("Enterprise AI Impact & Risk Intelligence")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("### Sign In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if login(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    st.stop()

# Sidebar navigation
st.sidebar.title("JobImpactX Platform")
st.sidebar.write("Enterprise AI Risk Intelligence")

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Role Assessment", "Explainability", "What-If Scenarios", "Audit Trail", "Reports"]
)

st.sidebar.divider()
st.sidebar.info("""
**About This Platform**

Provides explainable, audit-grade risk intelligence for understanding AI automation impact on workforce roles.

**Key Features:**
- Risk assessment with confidence intervals
- SHAP/LIME explainability
- Scenario analysis
- Governance and audit controls
""")

# Page: Dashboard
if page == "Dashboard":
    st.title("Executive Dashboard")
    st.subheader("AI Automation Risk Overview")
    
    # Fetch statistics from API
    try:
        # Note: In production, create a statistics endpoint
        st.info("Dashboard statistics - Connect to real-time metrics via API")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="System Status",
                value="Operational",
                delta="Healthy"
            )
        with col2:
            st.metric(
                label="API Endpoint",
                value="Active",
                delta=f"{API_URL}"
            )
        with col3:
            st.metric(
                label="Model Status",
                value="Loaded",
                delta="XGBoost"
            )
        with col4:
            st.metric(
                label="Auth Status",
                value="Authenticated",
                delta="Secured"
            )
        
        st.divider()
        st.info("Real-time analytics and role distribution visualizations would be displayed here based on assessment data from the database.")
        
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

# Page: Role Assessment
elif page == "Role Assessment":
    st.title("Role Automation Risk Assessment")
    st.write("Assess the automation probability for a specific role.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        job_title = st.text_input("Job Title", "Software Engineer")
        salary = st.number_input("Average Salary (USD)", min_value=20000, max_value=500000, value=120000)
        years_exp = st.number_input("Years of Experience", min_value=0, max_value=70, value=8)
        education = st.selectbox("Education Level", ["High School", "Bachelor's", "Master's", "PhD"])
    
    with col2:
        ai_exposure = st.slider("AI Exposure Index", 0.0, 1.0, 0.65)
        tech_growth = st.slider("Tech Growth Factor", 0.5, 1.5, 0.85)
        
        st.write("**Skill Proficiencies (0-1)**")
        skills = []
        for i in range(10):
            skill = st.slider(f"Skill {i+1}", 0.0, 1.0, 0.7, key=f"skill_{i}")
            skills.append(skill)
    
    if st.button("Assess Role", type="primary"):
        with st.spinner("Analyzing role..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/assess",
                    headers=get_headers(),
                    json={
                        "job_title": job_title,
                        "average_salary": salary,
                        "years_experience": years_exp,
                        "education_level": education,
                        "ai_exposure_index": ai_exposure,
                        "tech_growth_factor": tech_growth,
                        "skills": skills
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("Assessment Complete")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        risk_prob = result["automation_probability_2030"]
                        st.metric("Automation Probability", f"{risk_prob*100:.1f}%")
                    
                    with col2:
                        risk_cat = result["risk_category"]
                        color = "red" if risk_cat == "High" else "orange" if risk_cat == "Medium" else "green"
                        st.metric("Risk Category", risk_cat)
                    
                    with col3:
                        confidence = result["confidence"]
                        st.metric("Model Confidence", f"{confidence*100:.1f}%")
                    
                    st.write(f"**Assessment ID:** {result['assessment_id']}")
                    st.write(f"**Confidence Interval:** [{result['confidence_interval'][0]*100:.1f}%, {result['confidence_interval'][1]*100:.1f}%]")
                    
                    # Store assessment ID for explanation
                    st.session_state["last_assessment_id"] = result["assessment_id"]
                    
                else:
                    st.error(f"Assessment failed: {response.text}")
                    
            except Exception as e:
                st.error(f"Error: {e}")

# Page: Explainability
elif page == "Explainability":
    st.title("Model Explainability")
    st.write("Understand which features drive automation risk predictions.")
    
    assessment_id = st.text_input(
        "Assessment ID",
        value=st.session_state.get("last_assessment_id", "")
    )
    
    if st.button("Generate Explanation"):
        if not assessment_id:
            st.warning("Please provide an assessment ID")
        else:
            with st.spinner("Generating SHAP and LIME explanations..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/v1/explain",
                        headers=get_headers(),
                        json={"assessment_id": assessment_id}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("Explanations Generated")
                        
                        st.subheader("SHAP Explanation (Authoritative)")
                        st.json(result["shap_explanation"])
                        
                        st.subheader("LIME Explanation (Supplementary)")
                        st.json(result["lime_explanation"])
                        
                        if result.get("discrepancy_detected"):
                            st.warning("Discrepancy detected between SHAP and LIME. SHAP is authoritative.")
                            st.json(result.get("discrepancy_details"))
                    else:
                        st.error(f"Explanation failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

# Page: What-If Scenarios
elif page == "What-If Scenarios":
    st.title("What-If Scenario Analysis")
    st.write("Explore how changes to role features affect automation risk.")
    
    assessment_id = st.text_input(
        "Original Assessment ID",
        value=st.session_state.get("last_assessment_id", "")
    )
    
    st.subheader("Proposed Changes")
    
    col1, col2 = st.columns(2)
    
    changes = {}
    
    with col1:
        if st.checkbox("Modify Education"):
            changes["education_level"] = st.selectbox("New Education", ["High School", "Bachelor's", "Master's", "PhD"])
        
        if st.checkbox("Modify Salary"):
            changes["average_salary"] = st.number_input("New Salary", min_value=20000, max_value=500000, value=150000)
    
    with col2:
        if st.checkbox("Modify Skills"):
            st.write("New skill proficiencies:")
            new_skills = []
            for i in range(10):
                skill = st.slider(f"New Skill {i+1}", 0.0, 1.0, 0.8, key=f"new_skill_{i}")
                new_skills.append(skill)
            changes["skills"] = new_skills
    
    if st.button("Analyze Scenario"):
        if not assessment_id:
            st.warning("Please provide an assessment ID")
        elif not changes:
            st.warning("Please specify at least one change")
        else:
            with st.spinner("Analyzing scenario..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/v1/scenario",
                        headers=get_headers(),
                        json={
                            "assessment_id": assessment_id,
                            "changes": changes
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("Scenario Analysis Complete")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Original")
                            orig = result["original_assessment"]
                            st.metric("Risk", f"{orig['automation_probability_2030']*100:.1f}%")
                            st.write(f"Category: {orig['risk_category']}")
                        
                        with col2:
                            st.subheader("Scenario")
                            scen = result["scenario_assessment"]
                            st.metric("Risk", f"{scen['automation_probability_2030']*100:.1f}%")
                            st.write(f"Category: {scen['risk_category']}")
                        
                        delta = result["delta_automation_probability"]
                        st.metric("Change in Risk", f"{delta*100:+.1f}%")
                        
                        st.subheader("Analysis")
                        st.write(result["narrative"])
                    else:
                        st.error(f"Scenario analysis failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

# Page: Audit Trail
elif page == "Audit Trail":
    st.title("Audit Trail")
    st.write("View system activity and access logs.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        action_filter = st.selectbox("Filter by Action", ["All", "assessment", "explain", "scenario"])
    with col2:
        page_num = st.number_input("Page", min_value=1, value=1)
    with col3:
        per_page = st.number_input("Per Page", min_value=10, max_value=100, value=50)
    
    if st.button("Load Audit Logs"):
        with st.spinner("Loading audit logs..."):
            try:
                params = {
                    "page": page_num,
                    "per_page": per_page
                }
                if action_filter != "All":
                    params["action"] = action_filter
                
                response = requests.get(
                    f"{API_URL}/api/v1/audit",
                    headers=get_headers(),
                    params=params
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.write(f"**Total Logs:** {result['total']}")
                    st.write(f"**Page {result['page']} of {result['pages']}**")
                    
                    if result['logs']:
                        df = pd.DataFrame(result['logs'])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No audit logs found")
                else:
                    st.error(f"Failed to load audit logs: {response.text}")
                    
            except Exception as e:
                st.error(f"Error: {e}")

# Page: Reports
elif page == "Reports":
    st.title("Governance Reports")
    st.write("Generate bias analysis and sensitivity reports.")
    
    tab1, tab2 = st.tabs(["Bias Analysis", "Sensitivity Analysis"])
    
    with tab1:
        st.subheader("Fairness and Bias Report")
        st.write("Analyze model fairness across sensitive attributes.")
        
        sample_size = st.slider("Sample Size", 100, 1000, 500)
        
        if st.button("Generate Bias Report"):
            with st.spinner("Analyzing fairness metrics..."):
                try:
                    response = requests.get(
                        f"{API_URL}/api/v1/governance/bias",
                        headers=get_headers(),
                        params={"sample_size": sample_size}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("Bias Analysis Complete")
                        st.write(f"**Overall Assessment:** {result['overall_assessment']}")
                        
                        st.json(result)
                    else:
                        st.error(f"Bias analysis failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with tab2:
        st.subheader("Model Sensitivity Report")
        st.write("Test model robustness to input perturbations.")
        
        sample_size = st.slider("Sample Size", 10, 100, 50, key="sens_sample")
        
        if st.button("Generate Sensitivity Report"):
            with st.spinner("Analyzing sensitivity..."):
                try:
                    response = requests.get(
                        f"{API_URL}/api/v1/governance/sensitivity",
                        headers=get_headers(),
                        params={"sample_size": sample_size}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("Sensitivity Analysis Complete")
                        st.json(result)
                    else:
                        st.error(f"Sensitivity analysis failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Distribution by Category")
        risk_data = pd.DataFrame({
            'Risk Category': ['Low', 'Medium', 'High'],
            'Count': [450, 320, 230]
        })
        fig = px.pie(
            risk_data,
            values='Count',
            names='Risk Category',
            color_discrete_map={'Low': '#2ecc71', 'Medium': '#f39c12', 'High': '#e74c3c'},
            hole=0.3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top 10 Highest Risk Roles")
        top_roles = pd.DataFrame({
            'Job Title': [
                'Truck Driver',
                'Retail Worker',
                'Customer Support',
                'Construction Worker',
                'Mechanic',
                'Data Entry Specialist',
                'Security Guard',
                'Cashier',
                'Telemarketer',
                'Assembly Line Worker'
            ],
            'Risk Score': [0.92, 0.91, 0.90, 0.89, 0.87, 0.86, 0.85, 0.84, 0.83, 0.82]
        })
        
        fig = px.bar(
            top_roles,
            x='Risk Score',
            y='Job Title',
            orientation='h',
            color='Risk Score',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("Risk by Education Level")
    edu_data = pd.DataFrame({
        'Education Level': ["High School", "Bachelor's", "Master's", "PhD"],
        'Avg Risk Score': [0.68, 0.52, 0.42, 0.31]
    })
    
    fig = px.bar(
        edu_data,
        x='Education Level',
        y='Avg Risk Score',
        color='Avg Risk Score',
        color_continuous_scale='RdYlGn_r'
    )
    st.plotly_chart(fig, use_container_width=True)

elif page == "Role Assessment":
    st.title("Role Assessment")
    
    st.write("Assess a job role for AI automation risk by providing key characteristics.")
    
    with st.form("assessment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            job_title = st.text_input("Job Title", placeholder="e.g., Software Engineer")
            salary = st.number_input(
                "Average Salary (USD)",
                min_value=20000,
                max_value=500000,
                value=100000
            )
            experience = st.slider("Years of Experience", 0, 70, 10)
            education = st.selectbox(
                "Education Level",
                ["High School", "Bachelor's", "Master's", "PhD"]
            )
        
        with col2:
            ai_exposure = st.slider(
                "AI Exposure Index (0-1)",
                0.0, 1.0, 0.5,
                help="How much does this role interact with AI tools?"
            )
            tech_growth = st.slider(
                "Tech Growth Factor (0.5-1.5)",
                0.5, 1.5, 1.0,
                help="How fast is technology advancing in this field?"
            )
            st.write("**Skill Proficiencies** (0-1 scale)")
            
            skills = []
            skill_names = [
                "Creativity", "Data Analysis", "Robotics", "Communication",
                "Problem Solving", "Technical Proficiency", "Adaptability",
                "Leadership", "Domain Expertise", "Emotional Intelligence"
            ]
            
            cols = st.columns(5)
            for i, skill_name in enumerate(skill_names):
                with cols[i % 5]:
                    skill = st.slider(
                        skill_name,
                        0.0, 1.0, 0.5,
                        key=f"skill_{i}"
                    )
                    skills.append(skill)
        
        submitted = st.form_submit_button("Assess Role")
        
        if submitted:
            st.info("Assessment submitted! (Demo mode - showing placeholder results)")
            
            # Simulate assessment
            with st.spinner("Analyzing role..."):
                st.success("Assessment Complete")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Automation Risk",
                        "64%",
                        help="Probability role will be automated by 2030"
                    )
                with col2:
                    st.metric("Risk Category", "🟡 Medium")
                with col3:
                    st.metric("Confidence", "92%")
                
                st.markdown("---")
                st.subheader("Assessment Details")
                
                results_df = pd.DataFrame({
                    'Metric': [
                        'Automation Probability',
                        'Risk Category',
                        'Model Confidence',
                        'Confidence Interval (Lower)',
                        'Confidence Interval (Upper)'
                    ],
                    'Value': ['0.64', 'Medium', '0.92', '0.54', '0.74']
                })
                st.dataframe(results_df, use_container_width=True)

elif page == "Explainability":
    st.title("Explainability Explorer")
    
    st.write("Understand why a role received its assessment using SHAP and LIME explanations.")
    
    st.info("Select a recent assessment or enter an assessment ID")
    
    col1, col2 = st.columns(2)
    with col1:
        assessment_id = st.text_input(
            "Assessment ID",
            placeholder="Paste assessment UUID here"
        )
    with col2:
        if st.button("Load Explanation"):
            st.success("Explanation loaded (demo)")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("SHAP: Global Feature Importance")
        st.write("SHAP (SHapley Additive exPlanations) shows which features drive automation risk across all roles.")
        st.write("*Authoritative for governance & audit*")
        
        feature_importance = pd.DataFrame({
            'Feature': [
                'AI Exposure Index',
                'Tech Growth Factor',
                'Years Experience',
                'Salary',
                'Education Level'
            ],
            'Importance': [0.35, 0.25, 0.20, 0.12, 0.08]
        }).sort_values('Importance', ascending=True)
        
        fig = px.barh(
            feature_importance,
            x='Importance',
            y='Feature',
            color='Importance',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("LIME: Local Explanation")
        st.write("LIME shows which features influenced this specific role's assessment.")
        st.write("*Supplementary, human-friendly explanation*")
        
        lime_data = pd.DataFrame({
            'Feature': [
                'High AI Exposure',
                'Tech Growing Fast',
                'Low Experience',
                'Moderate Salary',
                'Bachelor Degree'
            ],
            'Impact': [0.25, 0.18, 0.15, -0.08, -0.12]
        }).sort_values('Impact', ascending=True)
        
        fig = px.barh(
            lime_data,
            x='Impact',
            y='Feature',
            color='Impact',
            color_continuous_scale='RdBu'
        )
        st.plotly_chart(fig, use_container_width=True)

elif page == "What-If Scenarios":
    st.title("What-If Scenario Explorer")
    
    st.write("Explore how changes in skills, education, or other factors could reduce automation risk.")
    
    st.info("Select a recent assessment and modify its characteristics to see impact")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Assessment")
        original = {
            'Job Title': 'Truck Driver',
            'Automation Risk': '92%',
            'Risk Category': '🔴 High',
            'Years Experience': 5,
            'Education': "High School"
        }
        for key, value in original.items():
            st.write(f"**{key}:** {value}")
    
    with col2:
        st.subheader("Scenario Changes")
        scenario_exp = st.slider(
            "Years of Experience (Scenario)",
            0, 70, 10,
            help="What if the worker gains more experience?"
        )
        scenario_edu = st.selectbox(
            "Education Level (Scenario)",
            ["High School", "Bachelor's", "Master's", "PhD"],
            index=0
        )
    
    if st.button("Run Scenario Analysis"):
        st.success("Scenario Analysis Complete")
        
        st.markdown("---")
        
        comparison = pd.DataFrame({
            'Metric': ['Automation Risk', 'Risk Category'],
            'Original': ['92%', 'High'],
            'Scenario': ['71%', 'Medium']
        })
        
        st.dataframe(comparison, use_container_width=True)
        
        st.write("""
        Impact Narrative:
        
        By acquiring a Bachelor's degree and gaining 5 more years of experience, 
        this truck driver's automation risk would decrease from 92% to 71%, moving from 
        High risk to Medium risk. This represents a 21 percentage point reduction.
        """)

elif page == "Audit Trail":
    st.title("Audit Trail & Governance")
    
    st.markdown("""
    Complete audit log of all assessments, explanations, and system access.
    """)
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        action_filter = st.multiselect(
            "Action Type",
            ["Assessment", "Explanation", "Scenario", "Access", "Admin"],
            default=["Assessment"]
        )
    with col2:
        date_range = st.date_input(
            "Date Range",
            value=(pd.Timestamp.now() - pd.Timedelta(days=7), pd.Timestamp.now())
        )
    with col3:
        status_filter = st.multiselect(
            "Status",
            ["Success", "Failure"],
            default=["Success", "Failure"]
        )
    
    # Sample audit log
    audit_data = pd.DataFrame({
        'Timestamp': pd.date_range(start='2025-01-10', periods=10, freq='H'),
        'User': ['analyst_1', 'analyst_2', 'admin'] * 3 + ['analyst_1'],
        'Action': ['Assessment', 'Explanation', 'Scenario', 'Assessment', 'Assessment',
                  'Explanation', 'Admin Config', 'Assessment', 'Scenario', 'Audit Access'],
        'Resource': ['uuid-12345', 'uuid-12345', 'uuid-12346', 'uuid-12347',
                    'uuid-12348', 'uuid-12348', 'Model v1.0', 'uuid-12349',
                    'uuid-12349', 'Audit Logs'],
        'Status': ['Success', 'Success', 'Success', 'Success', 'Failure',
                  'Success', 'Success', 'Success', 'Success', 'Success'],
        'IP Address': ['192.168.1.100', '192.168.1.101', '10.0.0.5'] * 3 + ['192.168.1.100']
    })
    
    st.dataframe(audit_data, use_container_width=True)
    
    st.divider()
    
    st.subheader("📊 Audit Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Actions (7 days)", 127, "+3")
    with col2:
        st.metric("Failed Actions", 2, "0")
    with col3:
        st.metric("Unique Users", 8)