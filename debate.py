from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title = "Debate Simulator", page_icon = "🗣️")
st.title("AI Debate Arena")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "round_count" not in st.session_state:
    st.session_state.round_count = 0
if "result_shown" not in st.session_state:
    st.session_state.result_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "debate_complete" not in st.session_state:
    st.session_state.debate_complete = False
if "name_entered" not in st.session_state:
    st.session_state.name_entered = False
if "evaluating" not in st.session_state:
    st.session_state.evaluating = False

def complete_setup():
    st.session_state.setup_complete = True

def show_result():
    st.session_state.result_shown = True

if not st.session_state.name_entered:

    st.subheader("Your information", divider = "rainbow")

    st.session_state["name"] = st.text_input(label = "Name", max_chars = 40, placeholder = "Enter your name")

    if st.session_state["name"]:
        st.session_state.name_entered = True

if not st.session_state.setup_complete:

    st.subheader("Debate setup", divider = "rainbow")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["topic"] = st.radio("Choose a topic", 
                        key = "visibility", options = [
                            "Is democracy the best form of government", 
                            "Is capitalism sustainable in the long term?", 
                            "Should the death penalty be abolished?", 
                            "Should euthanasia (assisted suicide) be legalised?", 
                            "Should recreational drugs be legalised?", 
                            "Does technology bring more harm than good?", 
                            "Is time travel ethically acceptable if it were possible?", 
                            "Should governments impose population control to save the planet?"])

    with col2:
        st.session_state["level"] = st.selectbox("Choose a difficulty level", options = [
                    "Easy", 
                    "Medium", 
                    "Hard"])

    st.markdown("""
    **Debate Rules:**
    - There will be **5 rounds** (you and the AI will alternate turns).
    - Keep your arguments clear and concise.
    - The AI will automatically evaluate both sides at the end. Good luck!
    """)

    if st.button("Start the debate", on_click = complete_setup):
        st.write("Setup complete. Starting the debate...")

if st.session_state.setup_complete and not st.session_state.result_shown and not st.session_state.debate_complete:

    st.info(f"The debate topic is: **{st.session_state['topic']}**. Please share your opening statement. Make sure you present your position clearly — are you ***for*** or ***against*** this topic?", icon = '🗣️')

    client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4"

    if not st.session_state.messages:
        st.session_state["messages"] = [{
            "role": "system", 
             "content": f"You are debating the user on the topic: {st.session_state['topic']}."
                f"The user is arguing the topic {st.session_state['topic'].lower()}; you must take the opposite stance."
                f"The debate difficulty is {st.session_state['level']}, so tailor your vocabulary, logic, and depth accordingly."
                f"The debate lasts exactly 5 rounds. Keep each turn concise, logical, and respectful."
                                        }]
    
    for message in st.session_state["messages"]:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    if st.session_state.round_count < 5:
        if prompt := st.chat_input("Your statement.", max_chars = 1000): # := means a combination of assignment symbol and : after if statement 
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                stream = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]],
                    stream=True
                )
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.round_count += 1
    else:
        st.session_state.debate_complete = True
        st.rerun()

if st.session_state.debate_complete and not st.session_state.result_shown:
      if not st.session_state.evaluating:
        if st.button("Show the result"):
            st.session_state.evaluating = True
            st.rerun()
            
if st.session_state.evaluating and not st.session_state.result_shown:
    st.write("Evaluating the debate results... Please wait.")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    result_client = OpenAI(api_key=st.secrets["OPEN_AI_KEY"])

    evaluation_prompt = f"""
        You are an impartial, expert debate judge evaluating a 5-round debate between a human user and an AI assistant.
        Your task:
        1. Read the entire debate transcript carefully.
        2. Evaluate both participants on these criteria:
        - Clarity of argument
        - Logical coherence and reasoning
        - Use of evidence or examples
        - Rebuttal quality (ability to address opponent’s points)
        - Persuasiveness and style consistency
        - Relevance to the selected **difficulty level** ({st.session_state['level']})

        3. Consider the declared topic and the debate transcript:
        - **Topic:** {st.session_state['topic']}
        - **Debate transcript:** (provided separately below)
        - The "user" represents the human debater.
        - The "assistant" represents the AI debater.
        - The debate lasted 5 rounds.
        
        4. Finally, decide the **winner**: either "User" or "AI".

        Be fair, objective, and professional. 
        Do not engage in further debate; only judge based on the transcript.

        Output Format (follow exactly):

        - User Score: <number>
        - AI Score: <number>
        - Winner: <User or AI>

        Feedback:
        <3–6 sentences explaining your reasoning and overall assessment>
        """
    
    result_completion = result_client.chat.completions.create(
        model = "gpt-4o",
        messages = [
            {"role": "system", "content": evaluation_prompt
             },
             {"role": "user", "content": f"This is the debate transcript to evaluate:\n\n{conversation_history}"}
        ])
    
    st.session_state.result_text = result_completion.choices[0].message.content
    st.session_state.result_shown = True
    st.session_state.evaluating = False

    st.rerun()

if st.session_state.result_shown:
    st.subheader("🏆Debate Result")
    st.write(st.session_state.result_text)

    if st.button("Start debating again", type = "primary"):
        streamlit_js_eval(js_expressions = "parent.window.location.reload()")


MAX_MESSAGES = 30
if len(st.session_state.messages) > MAX_MESSAGES:
    st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]
