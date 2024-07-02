##참고영상
#기본적인 streamlit ai assistant 구조 단순 text 답변 
#https://www.youtube.com/watch?v=mErptZiNaN0 : OpenAI Assistant API Quickstart: Streamlit & Python | Building a custom Cat AI in Just 13 Minutes


## terminal 에서 실행
## >> pip install streamlit
## >> streamlit run st_testBot.py

from openai import AzureOpenAI
import streamlit as st
import time
import os
import tempfile # 이미지 파일을 임시 저장하기 위해 모듈 사용
import requests  # 이미지 파일을 다운로드하기 위해 requests 모듈 사용
from PIL import Image  # 이미지를 열고 표시하기 위해 Pillow 모듈 사용
from io import BytesIO  # 바이트 데이터를 처리하기 위해 BytesIO 사용

#api 호출
import urllib.request

# json 모듈을 임포트합니다. json 모듈은 JSON 데이터를 처리하는 기능을 제공합니다.
import json
from datetime import datetime
from modules.functions import fabric_data_select, translate_to_eng


# 현재 시간 얻기    
current_time = datetime.now()
print(current_time)

# 환경 변수 설정 (Azure OpenAI 서비스의 API 엔드포인트, 키, 버전, 및 배포 이름) 
os.environ['AZURE_OPENAI_BASE'] = ''
os.environ['AZURE_OPENAI_KEY'] = ''
os.environ['AZURE_OPENAI_VERSION'] = ''
os.environ['AZURE_OPENAI_DEPLOYMENT_NAME'] = ''
os.environ['PROMPTFLOW_ENDPOINT_URL'] = ''
os.environ['PROMPTFLOW_ENDPOINT_KEY'] = ''


# 환경 변수로부터 API 정보 가져오기
#api_endpoint = os.getenv("AZURE_OPENAI_BASE")
#secrets.toml 에서 가져오는 방식으로 변경 
api_endpoint = st.secrets["AZURE_OPENAI_BASE"]
api_key = st.secrets["AZURE_OPENAI_KEY"]
api_version = st.secrets["AZURE_OPENAI_VERSION"]
api_deployment_name = st.secrets["AZURE_OPENAI_DEPLOYMENT_NAME"]
promptflow_endpoint_url = st.secrets["PROMPTFLOW_ENDPOINT_URL"]
promptflow_endpoint_key = st.secrets["PROMPTFLOW_ENDPOINT_KEY"]

# Assistant ID 설정
assistant_id = "asst_NmdmmOvcUjCI481bKEk4qFSE"

# Azure OpenAI 클라이언트 생성
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=api_endpoint,
)


### Assistant 가 호출하는 함수 기능 정의 START --------------------------------------------------------------------------------
### 현재 get_data_from_db() 함수는 사용하지 않고 있음. prompt flow endpoint 사용이 아니라 로컬에 함수 정의해서 사용

def get_data_from_db(user_query: str):
    data = {
        'question': user_query
        , 'qtype': 0
        , 'chat_history': []
    }
    body = str.encode(json.dumps(data))

    url = promptflow_endpoint_url
    # Replace this with the primary/secondary key, AMLToken, or Microsoft Entra ID token for the endpoint
    api_key = promptflow_endpoint_key
    if not api_key:
        raise Exception("A key should be provided to invoke the endpoint")

    # The azureml-model-deployment header will force the request to go to a specific deployment.
    # Remove this header to have the request observe the endpoint traffic rules
    headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ api_key), 'azureml-model-deployment': 'fabric-sql-generator-1' }

    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)
        result = response.read()
        #print(result)
        # JSON 문자열을 파싱하여 Python 객체로 변환
        response_dict = json.loads(result)
        # 'answer' 필드의 값을 utf-8 디코딩
        decoded_answer = response_dict['answer'].encode().decode('utf8')
        #print(decoded_answer)
        return decoded_answer
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))
        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))
        return str(error.code)

### Assistant 가 호출하는 함수 기능 정의 END --------------------------------------------------------------------------------
### Assistant requires_action인 경우 실행되는 함수 정의 --------------------------------------------------------------------------------
def get_outputs_for_tool_calls(tool_call):
    user_query = json.loads(tool_call.function.arguments)["user_query"]
    #sample_data = get_data_from_db(user_query=user_query)
    sample_data = fabric_data_select(user_query=user_query)
    return {
        "tool_call_id" : tool_call.id,
        #"output" : sample_data
        # JSON 객체를 문자열로 변환
        "output" : json.dumps(sample_data)
    }

### Assistant requires_action인 경우 실행되는 함수 정의 end --------------------------------------------------------------------------------




# Streamlit 세션 상태 초기화 (채팅 시작 여부 및 스레드 ID)
if "start_chat" not in st.session_state:
    st.session_state.start_chat = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# 페이지 설정 (제목 및 아이콘)
st.set_page_config(page_title="Azure OpenAI GPT", page_icon=":speech_balloon:")



# 사이드바의 "Start Chat" 버튼을 클릭하면 채팅 시작
if st.sidebar.button("Start Chat"):
    st.session_state.start_chat = True
    thread = client.beta.threads.create()  # 새로운 스레드 생성
    st.session_state.thread_id = thread.id  # 생성된 스레드의 ID 저장

# 페이지 제목 설정
st.title("chatGPT like chatbot")
st.write("this is sample text to be revised")


# "Exit Chat" 버튼을 클릭하면 채팅 종료
if st.button("Exit Chat"):
    st.session_state.messages = []  # 채팅 기록 초기화
    st.session_state.start_chat = False  # 채팅 상태 초기화
    st.session_state.thread_id = None  # 스레드 ID 초기화
    #이미지 임시 파일
    st.session_state.temp_files = []

# 채팅이 시작되었을 때 실행되는 코드
if st.session_state.start_chat:
    # 메시지 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "fabric DW 에 적재된 데이터로 차트를 생성할 수 있습니다!", "type": "string"}]

    # 세션 상태에 저장된 메시지를 화면에 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
        
            if message["type"] == "string":
                #st.markdown("str")
                st.markdown(message["content"])                
            elif message["type"] == "image_path":
                #st.markdown("image")
                st.image(Image.open(message["content"]))                


    # 사용자가 입력한 메시지를 처리 (prompt : 사용자가 하단 메시지 창에 입력하는 내용)
    if prompt := st.chat_input("default message?"):
        st.session_state.messages.append({"role": "user", "content": prompt, "type": "string"})  # 사용자 메시지 저장
        with st.chat_message("user"):
            st.markdown(prompt)

        # OpenAI 클라이언트에 메시지 생성 요청
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        # OpenAI 클라이언트에 채팅 실행 요청
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            max_prompt_tokens=50000,
            max_completion_tokens=50000,
            #force function calling
            tool_choice="auto"   ##"required"
        )

        # 실행 상태가 완료될 때까지 대기
        
        #while run.status != 'completed':
        #    time.sleep(1)
        #    run = client.beta.threads.runs.retrieve(
        #        thread_id=st.session_state.thread_id,
        #        run_id=run.id
        #    )
        placeholder = st.empty()
        pending = False
        while run.status != 'completed':
        #while run.status not in ['completed', 'queued']:
            if not pending:
                with placeholder.container():
                    with st.chat_message("assistant"):
                        st.markdown("Assistant is thinking...")
                pending = True
            
            
            if run.status == "requires_action":
                # 'run.required_action.submit_tool_outputs.tool_calls'에서 tool_calls를 가져옵니다
                tool_calls = run.required_action.submit_tool_outputs.tool_calls                
                # 'get_outputs_for_tool_calls' 함수를 'tool_calls'의 각 요소에 적용하여 tool_outputs를 생성합니다
                tool_outputs = map(get_outputs_for_tool_calls, tool_calls)
                # map 객체를 리스트로 변환하여 'tool_outputs'에 저장합니다
                tool_outputs = list(tool_outputs)
                # 'tool_outputs' 리스트를 출력합니다
                print("▶"*50)
                print(tool_outputs)
                
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id = st.session_state.thread_id,   # 현재 스레드의 ID
                    run_id = run.id,         # 현재 실행의 ID
                    tool_outputs = tool_outputs  # 생성된 도구 출력 목록
                )
            if run.status == "incomplete":
                print(run.incomplete_details)

            time.sleep(3)
            
            # 현재 run 상태를 다시 가져옴 
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
                )
            with placeholder.container():
                with st.chat_message("assistant"):
                    if run.status == "requires_action":
                        st.markdown("데이터를 검색중...")
                    if run.status in ["in_progress","queued"]:
                        st.markdown("진행중...")
                    else :
                        st.markdown(run.status)
                        
            #st.markdown("retrieve run" + run.status)

                

                #for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                #    f = tool_call.function
                #    f_name = f.name
                #    f_args = json.loads(f.arguments)
                #    tool_result = tool_to_function[f_name](**f_args)
                #    tools_output.append(
                #        {
                #            "tool_call_id" : tool_call.id,
                #            "output" : tool_result
                #        }
                #    )
        placeholder.empty()

        # 실행된 스레드의 메시지 목록 가져오기
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # 실행된 메시지 중 어시스턴트의 메시지를 필터링
        assistant_messages_for_run = [
            message for message in messages
            if message.run_id == run.id and message.role == "assistant"
        ]


        ## temp_file 경로 리스트 형태로 저장해두고 마지막 경로에서 삭제하는 로직 추가 필요함
        if 'temp_files' not in st.session_state:
            st.session_state.temp_files = []

        # 어시스턴트 메시지를 세션 상태에 저장하고 화면에 표시
        for message in reversed(assistant_messages_for_run):
            with st.chat_message("assistant"):
                for content in message.content:
                    if content.type == "text":
                        st.session_state.messages.append({"role": "assistant", "content": content.text.value, "type":"string"})  # 어시스턴트 메시지 저장
                        st.markdown(content.text.value)
                    elif content.type == "image_file" : 
                        image_file = content.image_file.file_id
                        #download image
                        image_data = client.files.content(image_file)
                        image_data = image_data.read() 
                        #print(type(image_data))    
                        # image_data 최종 타입은 byte | AttributeError: 'bytes' object has no attribute 'type'
                                              
                        #save image to temp file
                        temp_file = tempfile.NamedTemporaryFile(delete=False)
                        temp_file.write(image_data)
                        temp_file.close()
                        image = Image.open(temp_file.name)
                        st.session_state.messages.append({"role": "assistant", "content": temp_file.name, "type": "image_path"})
                        st.image(image)
else:
    # 채팅이 시작되지 않은 경우 화면에 표시되는 텍스트
    st.write("Click 'Start Chat' to begin")



