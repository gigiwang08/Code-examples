/* Group Members: Cecelia Shuai xshuai3, Gigi Wang ywang580 */ 
#include <iostream>
#include <string>
#include <vector>
#include <stdexcept>
#include "csapp.h"
#include "message.h"
#include "connection.h"
#include "client_util.h"

using std::cout;
void enter_loop(Connection &connection);

int main(int argc, char **argv) {
  if (argc != 5) {
    std::cerr << "Usage: ./receiver [server_address] [port] [username] [room]\n";
    return 1;
  }

  std::string server_hostname = argv[1];
  int server_port = std::stoi(argv[2]);
  std::string username = argv[3];
  std::string room_name = argv[4];

  // TODO: connect to server
  Connection connection;
  connection.connect(server_hostname, server_port);

  // TODO: send rlogin (expect a response from
  Message receiver_message = {TAG_RLOGIN, username};
  Message server_response;
  // send the message
  connection.send(receiver_message);
  // get server response
  connection.receive(server_response);
  // if server gives error to login message, quit
  if (server_response.tag == TAG_ERR) {
    fprintf(stderr, "%s", server_response.data.c_str());
    exit(1);
  }
  // TODO: and join messages
  receiver_message = {TAG_JOIN,room_name};
  // send message and get server response
  connection.send(receiver_message);
  connection.receive(server_response);
  // if server gives error to join message, quit
  if (server_response.tag == TAG_ERR) {
    fprintf(stderr, "%s", server_response.data.c_str());
    exit(1);
  }

  // TODO: loop waiting for messages from server
  //       (which should be tagged with TAG_DELIVERY)
  enter_loop(connection);
  return 0;
}

// helper function for loop
void enter_loop(Connection &connection) {
  Message receiver_message;
  while (true) {
    // if successfully received
    if (connection.receive(receiver_message)) {
      if(receiver_message.tag == TAG_DELIVERY) {
        cout << receiver_message.dissect_message();
      }
    } else{
      // prevent infinte loop when server dies:
      if (connection.get_last_result() == Connection::EOF_OR_ERROR) {
        exit(1);
      } else{
        fprintf(stderr, "%s\n", "Failure to receive message_receiver.");
      }
    }
  }
}