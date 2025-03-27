import socket
import json
import threading
import sys
import time
import os

class QuizClient:
    def __init__(self, host, port=5555):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player_name = ""
        self.connected = False
        self.game_started = False
        
    def clear_screen(self):
        """Xóa màn hình console."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def connect(self):
        """Kết nối đến server."""
        try:
            self.client_socket.connect((self.host, self.port))
            self.connected = True
            print("Đã kết nối đến server!")
            
            # Bắt đầu thread nhận tin nhắn
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            # Đăng ký tên người chơi
            self.register_player()
            
            # Vòng lặp chính để gửi tin nhắn
            while self.connected:
                time.sleep(0.1)
                
        except ConnectionRefusedError:
            print("Không thể kết nối đến server. Vui lòng kiểm tra lại địa chỉ IP và port.")
            return False
        except Exception as e:
            print(f"Lỗi: {e}")
            return False
        finally:
            self.client_socket.close()
            
        return True
        
    def register_player(self):
        """Đăng ký tên người chơi với server."""
        self.player_name = input("Nhập tên của bạn: ")
        self.send_message({"type": "register", "name": self.player_name})
        
    def send_message(self, message):
        """Gửi tin nhắn đến server."""
        try:
            self.client_socket.send(json.dumps(message).encode())
        except:
            print("Không thể gửi tin nhắn. Kết nối có thể đã bị đóng.")
            self.connected = False
            
    def receive_messages(self):
        """Nhận và xử lý tin nhắn từ server."""
        while self.connected:
            try:
                data = self.client_socket.recv(1024).decode()
                if not data:
                    break
                    
                message = json.loads(data)
                self.handle_message(message)
                
            except Exception as e:
                print(f"Lỗi khi nhận tin nhắn: {e}")
                self.connected = False
                break
                
    def handle_message(self, message):
        """Xử lý tin nhắn nhận được từ server."""
        msg_type = message.get("type", "")
        
        if msg_type == "welcome":
            print(message["message"])
            
        elif msg_type == "player_joined":
            print(f"Người chơi {message['name']} đã tham gia. Hiện có {message['count']}/4 người chơi.")
            
        elif msg_type == "player_left":
            print(f"Người chơi {message['name']} đã rời đi. Còn lại {message['count']} người chơi.")
            
        elif msg_type == "ready":
            print(message["message"])
            
        elif msg_type == "game_start":
            self.game_started = True
            self.clear_screen()
            print("===== TRÒ CHƠI BẮT ĐẦU =====")
            print("Danh sách người chơi:")
            for idx, player in enumerate(message["players"], 1):
                print(f"{idx}. {player}")
            print("============================")
            
        elif msg_type == "question":
            self.clear_screen()
            print(f"\nCâu hỏi {message['number']}/{message['total']}:")
            print(message["question"])
            for option in message["options"]:
                print(option)
                
            # Nhận câu trả lời từ người chơi
            answer = input("\nNhập câu trả lời của bạn (A/B/C/D): ").upper()
            while answer not in ["A", "B", "C", "D"]:
                answer = input("Vui lòng nhập A, B, C hoặc D: ").upper()
                
            self.send_message({"type": "answer", "answer": answer})
            print("Đã gửi câu trả lời. Đang chờ người chơi khác...")
            
        elif msg_type == "round_result":
            print("\n===== KẾT QUẢ =====")
            print(f"Đáp án đúng: {message['correct_answer']}")
            print("\nKết quả của người chơi:")
            for player, result in message["results"].items():
                status = "Đúng ✓" if result["correct"] else "Sai ✗"
                print(f"{player}: {result['answer']} - {status}")
                
            print("\nĐiểm số hiện tại:")
            for player, score in message["scores"].items():
                print(f"{player}: {score}")
            print("===================")
            
        elif msg_type == "game_over":
            self.clear_screen()
            print("\n===== TRÒ CHƠI KẾT THÚC =====")
            print("Điểm số cuối cùng:")
            for player, score in message["scores"].items():
                print(f"{player}: {score}")
                
            print("\nNgười chiến thắng:")
            for winner in message["winners"]:
                print(f"🏆 {winner} với {message['max_score']} điểm")
                
            print("\nCảm ơn đã tham gia trò chơi!")
            self.connected = False
            
        elif msg_type == "error":
            print(f"Lỗi: {message['message']}")
            self.connected = False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    else:
        server_ip = input("Nhập địa chỉ IP của server: ")
        
    client = QuizClient(server_ip)
    client.connect()