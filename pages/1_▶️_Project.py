import streamlit as st

import streamlit.components.v1 as components
#st.markdown("<h1 style='text-align: left; color: red;'>Some title</h1>", unsafe_allow_html=True)
st.title("Projects")
components.html('''
  <iframe title="■STANDARD_REPORT_법인세관리" width="900" height="541.25" src="https://app.powerbi.com/reportEmbed?reportId=90626f87-ac19-4494-b4db-cbb07204d256&autoAuth=true&ctid=f8838425-72ce-4840-88f1-b244354270b5" frameborder="0" allowFullScreen="true"></iframe>
 ''',height=500,width=3000)
#width=1920,height=1080
components.html('''
  <iframe title="px_naptha_20230510" width="900" height="541.25" src="https://app.powerbi.com/reportEmbed?reportId=e21fa649-95fa-4daa-8023-a51cdfb17be3&autoAuth=true&ctid=f8838425-72ce-4840-88f1-b244354270b5" frameborder="0" allowFullScreen="true"></iframe>
 ''',height=500,width=3000)
