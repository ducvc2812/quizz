import socket
import threading
import json
import random
import time

class QuizServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.clients = []
        self.players = {}
        self.scores = {}
        self.questions = []
        self.current_question = 0
        self.answers = {}
        self.game_started = False
        self.accepting_players = True
        self.load_questions()
        
    def load_questions(self):
        """Tải các câu hỏi mẫu."""
        self.questions = [
            {
                "question": "Thủ đô của Việt Nam là gì?",
                "options": ["A. Hồ Chí Minh", "B. Hà Nội", "C. Đà Nẵng", "D. Hải Phòng"],
                "correct": "B"
            },
            {
                "question": "Ngôn ngữ lập trình nào được sử dụng nhiều nhất trong AI?",
                "options": ["A. Java", "B. C++", "C. Python", "D. JavaScript"],
                "correct": "C"
            },
            {
                "question": "Đâu là hành tinh lớn nhất trong hệ mặt trời?",
                "options": ["A. Trái Đất", "B. Sao Hỏa", "C. Sao Mộc", "D. Sao Thổ"],
                "correct": "C"
            },
            {
                "question": "Ai là người sáng lập Microsoft?",
                "options": ["A. Steve Jobs", "B. Bill Gates", "C. Mark Zuckerberg", "D. Elon Musk"],
                "correct": "B"
            },
            {
                "question": "Biển nào lớn nhất thế giới?",
                "options": ["A. Thái Bình Dương", "B. Đại Tây Dương", "C. Ấn Độ Dương", "D. Bắc Băng Dương"],
                "correct": "A"
            }
        ]
        random.shuffle(self.questions)

    def start(self):
        """Khởi động server và lắng nghe kết nối."""
        self.server_socket.listen(10)  # Cho phép nhiều kết nối hơn để xử lý từ chối
        print(f"Server đang chạy tại địa chỉ {self.host}:{self.port}")
        print(f"Đang chờ người chơi tham gia...")
        
        # Tạo thread riêng để lắng nghe kết nối
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.daemon = True
        accept_thread.start()
        
        # Vòng lặp chính để nhận lệnh từ người điều hành
        while True:
            command = input()
            if command.lower() == 'start' and not self.game_started and len(self.clients) >= 1:
                self.accepting_players = False
                print("Bắt đầu trò chơi!")
                self.start_game()
            elif command.lower() == 'help':
                print("\nCác lệnh có sẵn:")
                print("start - Bắt đầu trò chơi")
                print("help - Hiển thị trợ giúp")
                print("status - Hiển thị trạng thái hiện tại\n")
            elif command.lower() == 'status':
                print(f"\nSố người chơi hiện tại: {len(self.clients)}/4")
                print("Danh sách người chơi:")
                for i, player in enumerate(self.players.values(), 1):
                    print(f"{i}. {player}")
                print(f"Trạng thái trò chơi: {'Đã bắt đầu' if self.game_started else 'Chưa bắt đầu'}\n")
    
    def accept_connections(self):
        """Thread riêng để xử lý kết nối từ client."""
        while self.accepting_players:
            try:
                client_socket, client_address = self.server_socket.accept()
                
                # Kiểm tra xem đã đủ 4 người chơi chưa
                if len(self.clients) >= 4 and not self.game_started:
                    client_socket.send(json.dumps({"type": "error", "message": "Đã đủ người chơi!"}).encode())
                    client_socket.close()
                    continue
                
                # Tạo thread mới để xử lý client
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                client_thread.daemon = True
                client_thread.start()
                
                # Nếu đã đủ 4 người chơi, hiển thị thông báo
                if len(self.clients) == 4 and not self.game_started:
                    print("\nĐã đủ 4 người chơi. Nhập 'start' để bắt đầu trò chơi.")
                    print("Nhập 'help' để xem các lệnh khác.\n")
            except Exception as e:
                print(f"Lỗi khi chấp nhận kết nối: {e}")
    
    def handle_client(self, client_socket, client_address):
        """Xử lý kết nối từ client."""
        try:
            client_socket.send(json.dumps({"type": "welcome", "message": "Chào mừng đến với Quiz Game!"}).encode())
            
            # Nhận thông tin đăng ký người chơi
            data = client_socket.recv(1024).decode()
            player_info = json.loads(data)
            player_name = player_info["name"]
            
            # Thêm người chơi vào danh sách
            self.clients.append(client_socket)
            self.players[client_socket] = player_name
            self.scores[player_name] = 0
            
            # Thông báo cho tất cả người chơi
            self.broadcast({"type": "player_joined", "name": player_name, "count": len(self.clients)})
            print(f"Người chơi {player_name} đã tham gia. Hiện có {len(self.clients)}/4 người chơi.")
            
            # Vòng lặp nhận dữ liệu từ client
            while not self.game_started:
                time.sleep(0.1)
            
            # Khi trò chơi bắt đầu, nhận câu trả lời từ người chơi
            while self.game_started:
                try:
                    data = client_socket.recv(1024).decode()
                    if not data:
                        break
                    
                    message = json.loads(data)
                    if message["type"] == "answer":
                        self.process_answer(client_socket, message["answer"])
                except:
                    break
                
        except Exception as e:
            print(f"Lỗi khi xử lý client: {e}")
        finally:
            # Xử lý khi người chơi ngắt kết nối
            if client_socket in self.clients:
                self.clients.remove(client_socket)
                player_name = self.players.pop(client_socket, "Unknown")
                if player_name in self.scores:
                    self.scores.pop(player_name)
                print(f"Người chơi {player_name} đã rời đi. Còn lại {len(self.clients)} người chơi.")
                self.broadcast({"type": "player_left", "name": player_name, "count": len(self.clients)})
            
            try:
                client_socket.close()
            except:
                pass
    
    def process_answer(self, client_socket, answer):
        """Xử lý câu trả lời từ người chơi."""
        if self.game_started and client_socket in self.players:
            self.answers[client_socket] = answer
            player_name = self.players[client_socket]
            print(f"Người chơi {player_name} đã trả lời: {answer}")
            
    def broadcast(self, message):
        """Gửi thông điệp đến tất cả người chơi."""
        encoded_message = json.dumps(message).encode()
        disconnected_clients = []
        
        for client in self.clients:
            try:
                client.send(encoded_message)
            except:
                disconnected_clients.append(client)
        
        # Xử lý các client đã ngắt kết nối
        for client in disconnected_clients:
            if client in self.clients:
                self.clients.remove(client)
                player_name = self.players.pop(client, "Unknown")
                if player_name in self.scores:
                    self.scores.pop(player_name)
                print(f"Người chơi {player_name} đã rời đi. Còn lại {len(self.clients)} người chơi.")
                
    def start_game(self):
        """Bắt đầu trò chơi."""
        self.game_started = True
        
        # Thông báo bắt đầu trò chơi
        self.broadcast({"type": "game_start", "players": list(self.scores.keys())})
        
        # Bắt đầu vòng câu hỏi đầu tiên
        self.current_question = 0
        self.next_round()
        
    def next_round(self):
        """Xử lý một vòng câu hỏi."""
        if self.current_question < len(self.questions):
            question_data = self.questions[self.current_question]
            
            # Gửi câu hỏi
            self.broadcast({
                "type": "question",
                "number": self.current_question + 1,
                "total": len(self.questions),
                "question": question_data["question"],
                "options": question_data["options"]
            })
            
            # Đợi câu trả lời
            self.answers = {}
            timeout = time.time() + 20
            while len(self.answers) < len(self.clients) and time.time() < timeout:
                time.sleep(0.1)
            
            # Kiểm tra đáp án và cập nhật điểm số
            correct_answer = question_data["correct"]
            results = {}
            
            for client, answer in self.answers.items():
                if client in self.players:
                    player_name = self.players[client]
                    is_correct = (answer.upper() == correct_answer)
                    
                    if is_correct:
                        self.scores[player_name] += 1
                        
                    results[player_name] = {
                        "answer": answer,
                        "correct": is_correct
                    }
            
            # Gửi kết quả
            self.broadcast({
                "type": "round_result",
                "correct_answer": correct_answer,
                "results": results,
                "scores": self.scores
            })
            
            # Tăng số câu hỏi và đợi 5 giây trước khi chuyển câu tiếp theo
            self.current_question += 1
            time.sleep(5)
            self.next_round()
        else:
            # Kết thúc trò chơi khi hết câu hỏi
            self.end_game()

    def end_game(self):
        """Kết thúc trò chơi và xác định người chiến thắng."""
        max_score = max(self.scores.values()) if self.scores else 0
        winners = [player for player, score in self.scores.items() if score == max_score]
        
        # Gửi kết quả cuối cùng
        self.broadcast({
            "type": "game_over",
            "scores": self.scores,
            "winners": winners,
            "max_score": max_score
        })
        
        print("\n===== TRÒ CHƠI KẾT THÚC =====")
        print("Điểm số cuối cùng:")
        for player, score in self.scores.items():
            print(f"{player}: {score}")
            
        print(f"\nNgười chiến thắng: {', '.join(winners)}")
        print("==============================\n")
        
        # Đóng tất cả kết nối
        for client in self.clients:
            try:
                client.close()
            except:
                pass
                
        # Khởi động lại server
        self.clients = []
        self.players = {}
        self.scores = {}
        self.current_question = 0
        self.answers = {}
        self.game_started = False
        self.accepting_players = True
        self.load_questions()
        
        print("Server đã được khởi động lại. Đang chờ người chơi tham gia...")

if __name__ == "__main__":
    server = QuizServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer đã dừng.")
    except Exception as e:
        print(f"Lỗi server: {e}")
