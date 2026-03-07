import streamlit as st


def init_session():
    """Inizializza il session state con i valori di default."""
    if "user_preferences" not in st.session_state:
        st.session_state.user_preferences = {
            "likes": [],
            "dislikes": [],
            "excluded_sources": [],
            "excluded_reasons": {},
            "category_time": {},
            "enabled_paid_sources": []
        }
    if "feed_index" not in st.session_state:
        st.session_state.feed_index = 0
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = None


def reset_session():
    """Resetta tutte le preferenze."""
    st.session_state.user_preferences = {
        "likes": [], "dislikes": [], "excluded_sources": [],
        "excluded_reasons": {}, "category_time": {},
        "enabled_paid_sources": []
    }
    st.session_state.feed_index = 0
    st.session_state.selected_category = None