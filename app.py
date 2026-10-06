import streamlit as st
st.title("My First Streamlit App")
name = st.text_input("Enter your name")
b = st.button("Click me")
if b and name:
    st.write(f"Hello, {name}!")