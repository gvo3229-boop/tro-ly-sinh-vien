import streamlit as st
from PIL import Image
import requests
import json
import base64

# --- DÁN GROQ API KEY CỦA BẠN VÀO ĐÂY ---
GROQ_API_KEY = "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"

st.title("🎓 Trợ lý Sinh viên: Quản lý Thời gian & Tài chính (Qwen 3.8)")
st.write("Ứng dụng quản lý thông minh sử dụng chung mô hình Qwen 3.8 trên Groq AI.")

tab1, tab2 = st.tabs(["💰 Quản lý Tài chính", "⏰ Quản lý Thời gian & Lịch học"])

# Hàm dùng chung Qwen 3.8 trên Groq (Hỗ trợ cả text và xử lý hình ảnh base64 nếu có)
def call_qwen_groq(messages_payload):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen/qwen3.8-27b",
        "messages": messages_payload,
        "temperature": 0.5
	"max_tokens": 500
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=60)
        if response.status_code == 200:
            res_json = response.json()
            return res_json['choices'][0]['message']['content']
        else:
            return f"Lỗi từ máy chủ Groq API ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Lỗi kết nối mạng: {str(e)}"

# --- TAB 1: QUẢN LÝ TÀI CHÍNH 1-1 ---
with tab1:
    st.header("Quy hoạch tài chính cá nhân & Tư vấn 1-1")
    
    col1, col2 = st.columns(2)
    with col1:
        current_balance = st.number_input("Nhập số dư hiện có (VNĐ):", min_value=0, value=1000000, step=50000, key="bal_1")
    with col2:
        target_days = st.number_input("Số ngày cần chi tiêu (Ví dụ: 15, 30 ngày):", min_value=1, value=30, step=1, key="days_1")
        
    uploaded_file = st.file_uploader("Tải lên ảnh hóa đơn tham khảo (Không bắt buộc)...", type=["jpg", "png", "jpeg"], key="file_1")
    
    receipt_context = "Không có hóa đơn cụ thể được tải lên."
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Hóa đơn đã tải lên', use_column_width=True)
        
        with st.spinner("Qwen 3.8 đang đọc hóa đơn..."):
            import io
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            payload = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hãy trích xuất số tiền, tên món hàng và tổng kết chi tiêu từ hóa đơn này:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                ]
            }]
            receipt_context = call_qwen_groq(payload)
            st.info(f"Kết quả đọc hóa đơn: {receipt_context}")

    if "finance_messages" not in st.session_state:
        st.session_state.finance_messages = []
        initial_prompt = f"""
        Bạn là một chuyên gia tư vấn tài chính cá nhân 1-1 thân thiện dành cho sinh viên. 
        Thông tin tài chính của sinh viên:
        - Tổng số dư: {current_balance:,.0f} VNĐ
        - Số ngày chi tiêu: {target_days} ngày
        - Thông tin hóa đơn/chi tiêu bổ sung: {receipt_context}
        Hãy chào sinh viên ngắn gọn và đưa ra cái nhìn tổng quan ban đầu cùng hạn mức chi tiêu trung bình mỗi ngày.
        """
        st.session_state.finance_messages.append({"role": "user", "content": initial_prompt})
        with st.spinner("Đang kết nối với Trợ lý tài chính..."):
            initial_reply = call_qwen_groq(st.session_state.finance_messages)
            st.session_state.finance_messages.append({"role": "assistant", "content": initial_reply})

    for message in st.session_state.finance_messages[1:]:
        with st.chat_message(message["role"]):
            content = message["content"]
            if isinstance(content, list):
                # Hiển thị phần text nếu nội dung là dạng multimodal payload
                for c in content:
                    if c.get("type") == "text":
                        st.write(c.get("text"))
            else:
                st.write(content)

    if user_query := st.chat_input("Nhập câu hỏi hoặc thắc mắc về tài chính...", key="chat_fin_input"):
        with st.chat_message("user"):
            st.write(user_query)
        st.session_state.finance_messages.append({"role": "user", "content": user_query})

        with st.spinner("Trợ lý đang trả lời..."):
            ai_response = call_qwen_groq(st.session_state.finance_messages)
            with st.chat_message("assistant"):
                st.write(ai_response)
            st.session_state.finance_messages.append({"role": "assistant", "content": ai_response})

# --- TAB 2: QUẢN LÝ THỜI GIAN 1-1 ---
with tab2:
    st.header("Lên lịch trình thông minh & Tư vấn 1-1")
    
    option = st.radio(
        "Chọn cách nhập lịch học:", 
        ["Nhập văn bản thủ công", "Tải lên file lịch (.ics, .csv, .txt)", "📸 Tải lên ảnh Thời khóa biểu (JPG, PNG)"], 
        key="opt_2"
    )
    schedule_data = ""
    
    if option == "Nhập văn bản thủ công":
        schedule_data = st.text_area("Nhập lịch học hoặc deadline của bạn (Ví dụ: Thứ 2 học Toán 7h-9h...):", key="txt_2")
        
    elif option == "Tải lên file lịch (.ics, .csv, .txt)":
        uploaded_schedule_file = st.file_uploader("Tải lên file lịch học", type=["txt", "csv", "ics"], key="file_2")
        if uploaded_schedule_file is not None:
            try:
                raw_text = uploaded_schedule_file.getvalue().decode("utf-8", errors="ignore")
                if "BEGIN:VEVENT" in raw_text:
                    events = []
                    for line in raw_text.splitlines():
                        if any(k in line for k in ["SUMMARY:", "DTSTART:", "DTEND:", "LOCATION:"]):
                            events.append(line)
                    schedule_data = "\n".join(events)
                    if not schedule_data.strip():
                        schedule_data = raw_text[:4000]
                else:
                    schedule_data = raw_text[:4000]
                    
                st.info("Đã xử lý file thành công!")
            except Exception as e:
                st.error(f"Không thể đọc file này: {e}")

    else: # Quét ảnh Thời khóa biểu trực tiếp bằng Qwen 3.8 Vision
        uploaded_img = st.file_uploader("Tải lên ảnh Thời khóa biểu của bạn...", type=["jpg", "png", "jpeg"], key="img_schedule")
        if uploaded_img is not None:
            image = Image.open(uploaded_img)
            st.image(image, caption='Ảnh thời khóa biểu đã tải lên', use_column_width=True)
            
            with st.spinner("Qwen 3.8 đang đọc thông tin từ ảnh Thời khóa biểu..."):
                import io
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                payload = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Hãy đọc và trích xuất lại toàn bộ thông tin môn học, thứ, ngày, giờ học, phòng học từ ảnh thời khóa biểu này thành dạng văn bản rõ ràng:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                    ]
                }]
                schedule_data = call_qwen_groq(payload)
                st.success("Đã quét thành công Thời khóa biểu từ ảnh!")
                st.text_area("Thông tin trích xuất từ ảnh:", value=schedule_data, height=150)

    # Nút bắt đầu trò chuyện 1-1 cho Lịch học
    if st.button("🚀 Bắt đầu trò chuyện & Lên thời gian biểu", key="btn_start_time"):
        if not schedule_data.strip():
            st.warning("Vui lòng nhập lịch, tải file hoặc upload ảnh thời khóa biểu trước!")
        else:
            initial_time_prompt = f"""
            Bạn là một trợ lý quản lý thời gian và lập thời gian biểu học tập chuyên nghiệp 1-1 dành cho sinh viên.
            Dưới đây là thông tin thời khóa biểu/lịch học của sinh viên:
            
            {schedule_data}
            
            Hãy tổng hợp ngắn gọn các môn học/mốc thời gian quan trọng, đề xuất thời gian biểu khoa học (gồm cả giờ tự học và nghỉ ngơi), sau đó sẵn sàng giải đáp và điều chỉnh lịch trình theo yêu cầu tiếp theo của sinh viên.
            """
            st.session_state.time_messages = [
                {"role": "user", "content": initial_time_prompt}
            ]
            with st.spinner("Trợ lý đang phân tích lịch và chuẩn bị thời gian biểu..."):
                initial_time_reply = call_qwen_groq(st.session_state.time_messages)
                st.session_state.time_messages.append({"role": "assistant", "content": initial_time_reply})

    # Khung trò chuyện 1-1
    if "time_messages" in st.session_state and len(st.session_state.time_messages) > 0:
        st.write("---")
        st.subheader("💬 Trò chuyện 1-1 với Trợ lý Lịch học")
        
        for message in st.session_state.time_messages[1:]:
            with st.chat_message(message["role"]):
                content = message["content"]
                if isinstance(content, list):
                    for c in content:
                        if c.get("type") == "text":
                            st.write(c.get("text"))
                else:
                    st.write(content)

        if time_user_query := st.chat_input("Nhập yêu cầu điều chỉnh lịch trình...", key="chat_time_input"):
            with st.chat_message("user"):
                st.write(time_user_query)
            st.session_state.time_messages.append({"role": "user", "content": time_user_query})

            with st.spinner("Trợ lý đang điều chỉnh thời gian biểu..."):
                time_ai_response = call_qwen_groq(st.session_state.time_messages)
                with st.chat_message("assistant"):
                    st.write(time_ai_response)
                st.session_state.time_messages.append({"role": "assistant", "content": time_ai_response})