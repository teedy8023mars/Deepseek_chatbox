import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import threading
import requests
import json
import queue
import re

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek R1")
        self.root.geometry("1000x600")

        # Global parameters with default values
        self.global_params = {
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 50
        }

        # Queue for storing text to be displayed from child threads
        self.msg_queue = queue.Queue()

        # Chat history area
        self.chat_area = scrolledtext.ScrolledText(root, state='disabled', wrap='word')
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure tags for left/right alignment and waiting status
        self.chat_area.tag_configure("left", justify="left")
        self.chat_area.tag_configure("right", justify="right", foreground='#2E7D32')
        self.chat_area.tag_configure("waiting", foreground='#2FA7ED')
        self.chat_area.tag_configure("system", foreground='#808080')
        self.chat_area.tag_configure("model", foreground='#08479B')
        self.chat_area.tag_configure("time_taken", foreground='#666666', font=('Arial', 9))
        
        # 设置聊天区域的背景色和字体
        self.chat_area.configure(
            bg='#F5F5F5',
            font=('Arial', 11),
            padx=10,
            pady=5
        )

        # Store the position of the last message
        self.last_message_start = "1.0"
        
        # Control variables for waiting animation
        self.waiting_animation = False
        self.dots_count = 0
        self.waiting_start_time = None  # 添加计时起始时间变量

        # Bottom toolbar: model selection dropdown, input box, send button
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Model dropdown menu
        self.available_models = [
            "deepseek-r1:14b",
            "deepseek-r1:7b",
            "deepseek-r1:8b",
            "deepseek-r1:1.5b",
        ]
        # Default selection: "deepseek-r1:1.5b"
        self.selected_model = tk.StringVar(value=self.available_models[3])
        self.model_menu = tk.OptionMenu(bottom_frame, self.selected_model, *self.available_models)
        self.model_menu.config(width=15)
        self.model_menu.pack(side=tk.LEFT, padx=5)

        # Input box
        self.input_area = tk.Text(bottom_frame, height=3, width=40, bd=2, relief="solid")
        self.input_area.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Send button
        self.send_button = tk.Button(bottom_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.input_area.bind('<Return>', self.send_message_event)

        # Check queue every 100ms
        self.root.after(100, self.check_queue)

        # Insert welcome message
        self._update_chat("Welcome to DeepSeek ChatBox!", 'left', is_system=True)
        self._update_chat("Available parameters (format: param=value):\n" + 
                         "- temperature: Controls randomness (0.0-1.0)\n" +
                         "- top_p: Controls sampling probability (0.0-1.0)\n" +
                         "- top_k: Controls sampling range (1-100)\n" +
                         f"Current settings: temperature={self.global_params['temperature']}, " +
                         f"top_p={self.global_params['top_p']}, top_k={self.global_params['top_k']}", 'left', is_system=True)

    def check_queue(self):
        """Main thread periodically checks queue and inserts messages into chat box"""
        while not self.msg_queue.empty():
            msg, align = self.msg_queue.get()
            self._update_chat(msg, align)
        self.root.after(100, self.check_queue)

    def _update_chat(self, message, align='left', waiting=False, is_system=False):
        """Update chat box function, supports updating the last message"""
        self.chat_area.config(state='normal')
        
        if waiting:
            if not hasattr(self, 'current_waiting_line'):
                self.chat_area.insert(tk.END, message + "\n", (align, "waiting"))
                self.current_waiting_line = self.chat_area.index("end-2c linestart")
            else:
                self.chat_area.delete(self.current_waiting_line, self.chat_area.index(self.current_waiting_line + " lineend"))
                self.chat_area.insert(self.current_waiting_line, message, (align, "waiting"))
        else:
            if align == 'left' and hasattr(self, 'current_waiting_line'):
                self.chat_area.delete(self.current_waiting_line, self.chat_area.index(self.current_waiting_line + " lineend"))
                tags = (align, "system") if is_system else (align, "model")
                self.chat_area.insert(self.current_waiting_line, message, tags)
                delattr(self, 'current_waiting_line')
            else:
                if align == ('time_taken', 'inline'):
                    # 只插入时间信息
                    self.chat_area.insert(tk.END, message + "\n", 'time_taken')
                elif isinstance(align, tuple):  # 处理带有多个标签的消息
                    self.chat_area.insert(tk.END, message + "\n", align)
                else:
                    tags = (align, "system") if is_system else (align, "model") if align == 'left' else (align,)
                    self.chat_area.insert(tk.END, message + "\n", tags)
            
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    def animate_waiting(self):
        """Update waiting animation with elapsed time"""
        if self.waiting_animation:
            self.dots_count = (self.dots_count + 1) % 3
            elapsed_time = int((datetime.now() - self.waiting_start_time).total_seconds())  # 转换为整数
            waiting_msg = f"{self.current_model} ({self.waiting_timestamp}): Thinking{'.' * (self.dots_count + 1)} ({elapsed_time}s)"
            self._update_chat(waiting_msg, 'left', waiting=True)
            self.root.after(1000, self.animate_waiting)  # 改为1000ms刷新

    def enable_input(self):
        """Re-enable input box and send button"""
        self.input_area.config(state='normal')
        self.send_button.config(state='normal')
        
    def disable_input(self):
        """Disable input box and send button"""
        self.input_area.config(state='disabled')
        self.send_button.config(state='disabled')

    def send_message(self):
        raw_input_text = self.input_area.get("1.0", tk.END).strip()
        if not raw_input_text:
            return
        self.input_area.delete("1.0", tk.END)

        # Check if user input is a parameter setting command, format: temperature=1.2
        param_match = re.fullmatch(r"(\w+)\s*=\s*([\d\.]+)", raw_input_text)
        if param_match:
            key = param_match.group(1)
            try:
                # Convert value to float or int
                value = float(param_match.group(2))
            except:
                value = param_match.group(2)
            # Update global parameters
            self.global_params[key] = value
            timestamp = datetime.now().strftime("%H:%M:%S")
            # Display success message in chat box (left-aligned)
            self._update_chat(f"[SYSTEM ({timestamp})] Set {key} = {value}", 'left', is_system=True)
            return

        # Normal dialogue input: display text in chat box (right-aligned)
        timestamp = datetime.now().strftime("%H:%M:%S")
        user_msg = f"You ({timestamp}): {raw_input_text}"
        self._update_chat(user_msg, 'right')

        # Disable input box and send button
        self.disable_input()

        # Reset waiting line position to ensure new waiting message creation
        if hasattr(self, 'current_waiting_line'):
            delattr(self, 'current_waiting_line')

        # Get current selected model and start waiting animation
        self.current_model = self.selected_model.get()
        self.waiting_timestamp = datetime.now().strftime("%H:%M:%S")
        self.waiting_animation = True
        self.dots_count = 0
        self.waiting_start_time = datetime.now()  # 记录开始时间
        self.animate_waiting()

        # Start child thread to send request with global parameters
        threading.Thread(target=self.get_deepseek_reply, args=(raw_input_text, self.current_model, self.global_params.copy()), daemon=True).start()

    def get_deepseek_reply(self, user_input, model_name, params):
        try:
            url = "http://localhost:11434/api/generate"
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": model_name,
                "prompt": user_input,
                "stream": False
            }
            payload.update(params)
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
            
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get('response', '')
                reply_clean = re.sub(r"<think>.*?</think>\s*", "", reply, flags=re.DOTALL)
                timestamp = datetime.now().strftime("%H:%M:%S")
                final_reply = f"{model_name} ({timestamp}): {reply_clean}"
                
                # 计算耗时
                elapsed_time = int((datetime.now() - self.waiting_start_time).total_seconds())
                
                # Stop waiting animation
                self.waiting_animation = False
                # Use message queue to send reply
                self.msg_queue.put((final_reply, 'left'))
                
                # 只显示时间信息
                time_info = f"(Time Taken: {elapsed_time}s)"
                self.msg_queue.put((time_info, ('time_taken', 'inline')))
                
                # Re-enable input in main thread
                self.root.after(1, self.enable_input)
            else:
                self.waiting_animation = False
                error_msg = f"{model_name}: API Error (HTTP {resp.status_code})"
                self.msg_queue.put((error_msg, 'left'))
                self.root.after(1, self.enable_input)
        except Exception as e:
            self.waiting_animation = False
            error_msg = f"{model_name}: Error - {str(e)}"
            self.msg_queue.put((error_msg, 'left'))
            self.root.after(1, self.enable_input)

    def check_queue(self):
        """Main thread periodically checks queue and inserts messages into chat box"""
        while not self.msg_queue.empty():
            msg_item = self.msg_queue.get()
            if isinstance(msg_item, tuple) and len(msg_item) >= 2:
                msg, align = msg_item[0], msg_item[1]
                self._update_chat(msg, align)
            # Ensure input is enabled after message display
            if not self.waiting_animation:
                self.enable_input()
        self.root.after(100, self.check_queue)

    def send_message_event(self, event):
        """Handle Return key press event"""
        self.send_message()
        return "break"  # Prevents the default newline behavior

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
