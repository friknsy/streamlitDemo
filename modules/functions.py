import streamlit as st
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


import json
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from langchain_openai import AzureChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
#from langchain_community.agent_toolkits import create_sql_agent


#모델 선언
azure_llm =AzureChatOpenAI(
    ## 랭체인 안의 매개 변수들
    api_key           = st.secrets["AZURE_OPENAI_KEY"],
    azure_endpoint    = st.secrets["AZURE_OPENAI_BASE"],
    api_version       = st.secrets["AZURE_OPENAI_VERSION"],
    azure_deployment  = st.secrets["AZURE_OPENAI_DEPLOYMENT_NAME"],
)

_username =        st.secrets["FABRIC_USERNAME"]
_password =        st.secrets["FABRIC_PASSWORD"]
_fabric_endpoint = st.secrets["FABRIC_ENDPOINT"]
_fabric_database = st.secrets["FABRIC_DATABASE"]
_odbc_driver = st.secrets["ODBC_DRIVER"]

#connection_string = f"mssql+pyodbc://@{fabric_endpoint}/DWforAiStudio?driver=ODBC+Driver+17+for+SQL+Server"
#---------------------login time out error 발생. streamlit cloud linux 서버에서 
#---------------------port 번호 fabric.microsoft.com:1433 (X) fabric.microsoft.com,1433 방식으로 넘김.

connection_url = URL.create(
    "mssql+pyodbc",
    username = _username,
    password = _password,
    host = _fabric_endpoint,
    port = 1433,
    database = _fabric_database,
    query={
        "driver":_odbc_driver ,
        "TrustServerCertificate": "yes",
        "authentication": "ActiveDirectoryPassword",
    },
)
print(connection_url)
engine = create_engine(connection_url)

_include_tables = [
                    'DIM_CUSTOMER'
                    #, 'DIM_DATE'
                    #, 'DIM_DATE_COPY'
                    #, 'DIM_PRODUCT'
                    #, 'Geography'
                    #, 'HackneyLicense'
                    #, 'Medallion'
                    #, 'SALES'
                    #, 'TERRITORY'
                    #, 'Time'
                    #, 'Trip'
                    #, 'Weather'
                    , 'diabetes'
                    , 'stock_nvidia'
                    #, 'stock_samsung'
                    #, 'titanic'
]


db = SQLDatabase(
                    engine
                    , schema="dbo"
                    , lazy_table_reflection=True
                    , include_tables=_include_tables
                    , custom_table_info=[]
)

##쿼리생성
def fabric_data_select(user_query: str):

    query_eng = translate_to_eng(user_query)
    chain = create_sql_query_chain(azure_llm, db)
    query_eng = query_eng  + "Always use top 100 in sql" + "Select all necessary columns considering that this is data for chart creation"
    response = chain.invoke({"question": query_eng})
    print(response)

    with engine.connect() as conn:
        reulst = conn.execute(text(response)).mappings()
        # 쿼리 결과 출력
        rows = reulst.fetchall()
        ## RowMapping 객체를 딕셔너리로 변환
        #result_dicts = [dict(row) for row in rows        
        ## JSON으로 변환
        #json_output = json.dumps(result_dicts, default=str)  # datetime 객체 등을 문자열로 변환하기 위해 default=str 사용
        ###print(json_output)
        # 상위 코드 json_output 에서 헤더가 반복됨. 헤더를 최초한번 표현하도록 코드 수정정
        if rows:
            # 열 헤더 추출
            headers = list(rows[0].keys())
            # 데이터만 추출
            data = [list(row.values()) for row in rows]
            # 새로운 JSON 구조 생성
            json_output = json.dumps({"headers": headers, "data": data}, default=str)
            return json_output
        else:
            # 결과가 없는 경우 빈 JSON 반환
            return json.dumps({"headers": [], "data": []})
        

        
## 함수정의 | 사용자 질문 영어 번역 (영어로 질문 시 답변정확도 향상)
def translate_to_eng(user_message: str)-> str : 
    #프롬프트 작성
    print(user_message)
    prompt = ChatPromptTemplate.from_template( 
            """
            You are the translator and only output the translated results.
            If user input is {trans_from}, translate it to {trans_to} 
            so that the meaning does not change.
            If user input is not {trans_from}, answer as is without translating.
            this is the user input : {input}
            """
            )
    llm = azure_llm
    # chain 연결 (LCEL)
    chain = prompt | llm
    # chain 호출
    response = chain.invoke({"input": user_message, "trans_from":"Korean", "trans_to": "English"})
    return response.content    


#print(translate_to_eng("2023년 3월 엔비디아 거래량"))
#print(fabric_data_select("2023년 3월 24일과 27일의 엔비디아 거래량"))
