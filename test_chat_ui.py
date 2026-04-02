import streamlit as st
st.markdown("some content")
c = st.container()
with c:
    st.write("Inside container")
    # let's try chat input inside container
    msg = st.chat_input("Ask anything")
    if msg:
        st.write("You said:", msg)
