import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import requests
import os

# Configure page
st.set_page_config(
    page_title="AI Job Impact Platform",
    page_icon="",
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
    .risk-low {
        color: #2ecc71;
        font-weight: bold;
    }
    .risk-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .risk-high {
        color: #e74c3c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("AI Job Impact Platform")
st.sidebar.write("Version 1.0.0")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Role Assessment", "Explainability", "What-If Scenarios", "Audit Trail"]
)

st.sidebar.divider()
st.sidebar.info("""
**About This Platform**

This platform helps organizations understand and govern the impact of AI-driven automation on their workforce roles.

**Key Features:**
- Role-level automation risk assessment
- SHAP/LIME explainability framework
- What-if scenario analysis
- Audit trail and governance controls
""")

# Main content
if page == "Dashboard":
    st.title("Executive Dashboard")
    
    st.subheader("AI Automation Risk Overview")
    st.write("Predicted impact of AI-driven automation on your workforce by 2030.")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Avg Risk Score",
            value="0.54",
            delta="-0.02",
            delta_color="inverse"
        )
    with col2:
        st.metric(
            label="High Risk Roles",
            value="127",
            delta="+5",
            delta_color="inverse"
        )
    with col3:
        st.metric(
            label="Model Confidence",
            value="92%",
            delta="+2%"
        )
    with col4:
        st.metric(
            label="Last Updated",
            value="2 hours ago"
        )
    
    st.divider()
    
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