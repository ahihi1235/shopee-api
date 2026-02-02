import streamlit as st

st.write("### Kiểm tra kết nối iPhone")
st.success("Nếu bạn thấy dòng này, nghĩa là hệ thống Streamlit vẫn hoạt động bình thường trên iPhone của bạn.")

if st.button("Bấm thử"):
    st.balloons()

# Không thêm bất kỳ dòng CSS markdown nào ở đây để test
