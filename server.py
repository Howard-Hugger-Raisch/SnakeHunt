import pickle
import socket
from threading import Thread

from gamedata import *
import comm
from game import *

class Server():
    def __init__(self):
        self.game = Game(self)
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = 5555
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.next_id = 0
        
    def start(self):
        try:
            self.s.bind((self.host, self.port))
        except socket.error as e:
            print("Error binding.", e)

        self.s.listen(5)
        Thread(target=self.game.game_loop).start()
        print("Server started.")
        print(f"Server IP: {self.host} Server Port: {self.port}")

    def listen(self):
        while True:
            sock, addr = self.s.accept()
            if not self.game.running:
                break
            print("Connected to:", addr)

            position = self.game.get_random_position()
            snake = Snake(position, Snake.INITIAL_LENGTH, 1, 0, self.game.bounds)
            player = Player(self.next_id, snake, sock)
            self.next_id = self.next_id + 1

            Thread(target=self.player_handler, args=(player,)).start()

    def receive_name(self, player):
        while True:
            # Receive name input or quit signal
            input_size_as_bytes = comm.receive_data(player.socket, comm.MSG_LEN)
            input_size = comm.to_int(input_size_as_bytes)
            input = pickle.loads(comm.receive_data(player.socket, input_size))

            # Client quit during name selection
            if input == comm.Message.QUIT:
                return False

            name_accepted = False

            # The name is either valid, too long, or already used.
            response = None
            if len(input) > MAX_NAME_LENGTH:
                response = pickle.dumps(comm.Message.NAME_TOO_LONG)
            else:
                for pl in self.game.players:
                    if pl.name == input:
                        response = pickle.dumps(comm.Message.NAME_USED)
                        break
            if response == None:
                response = pickle.dumps(comm.Message.NAME_OK)
                player.name = input
                name_accepted = True

            # Tell client if name was valid, too long, or already used
            size_as_bytes = comm.size_as_bytes(response)
            comm.send_data(player.socket, size_as_bytes)
            comm.send_data(player.socket, response)

            if name_accepted:
                return True

            # If the name was too long, send a message to client indicating max allowed length
            if len(input) > MAX_NAME_LENGTH:
                max_length = pickle.dumps(MAX_NAME_LENGTH)
                size_as_bytes = comm.size_as_bytes(max_length)
                comm.send_data(player.socket, size_as_bytes)
                comm.send_data(player.socket, max_length)

    def receive_input(self, player):
        
        while self.game.running:
            try:
                input_size_as_bytes = comm.receive_data(player.socket, comm.MSG_LEN)
                input_size = comm.to_int(input_size_as_bytes)
                input = pickle.loads(comm.receive_data(player.socket, input_size))
                print(input)
            except:
                self.game.remove_player(player)
                break
            if input == comm.Message.QUIT:
                self.game.remove_player(player)
                break
            player.snake.change_direction(input)

    def player_handler(self, player):
        if not self.receive_name(player): return
        self.game.add_player(player)
        self.receive_input(player)

    def send_game_data(self, player, game_data_serialized):
        size = comm.size_as_bytes(game_data_serialized)
        comm.send_data(player.socket, size)
        comm.send_data(player.socket, game_data_serialized)

    # Before exiting, send a message to all players notifying them that the server will shutdown
    # Close each player's socket connection
    # Connect a dummy socket to stop the listening thread from hanging on the socket.accept() call
    def on_exit(self):
        self.game.running = False
        shutdown_msg = pickle.dumps(comm.Message.SERVER_SHUTDOWN)
        shutdown_msg_length = comm.size_as_bytes(shutdown_msg)
        for player in self.game.players:
            comm.send_data(player.socket, shutdown_msg_length)
            comm.send_data(player.socket, shutdown_msg)

        terminator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        terminator_socket.connect((self.host, self.port))
        
    # Prompt the user to shutdown the server by typing 'exit'
    def listen_exit(self):
        while self.game.running:
            print('Enter \'exit\' to shutdown server')
            user_input = input()
            if user_input.lower() == 'exit':
                self.on_exit()

def main():
    server = Server()
    server.start()
    Thread(target=server.listen).start()
    server.listen_exit()

if __name__ == '__main__':
    main()
