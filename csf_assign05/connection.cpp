/* Group Members: Cecelia Shuai xshuai3, Gigi Wang ywang580 */ 
#include <sstream>
#include <cctype>
#include <cassert>
#include "csapp.h"
#include "message.h"
#include "connection.h"

#include <string>

using std::string;

Connection::Connection()
  : m_fd(-1)
  , m_last_result(SUCCESS) {
}

Connection::Connection(int fd)
  : m_fd(fd)
  , m_last_result(SUCCESS) {
  // TODO: call rio_readinitb to initialize the rio_t object
  rio_readinitb(&m_fdbuf, fd);
}

void Connection::connect(const std::string &hostname, int port) {
  // TODO: call open_clientfd to connect to the server
  string port_str = std::to_string(port);
  int fd = open_clientfd(hostname.c_str(), port_str.c_str());
  if (fd < 0) {
    // unable to connect to the server, send error message and quit
    fprintf(stderr, "%s\n", "Could not connect to server");
    exit(1);
  }
  // update m_fd if successfully conencted
  m_fd = fd;
  // TODO: call rio_readinitb to initialize the rio_t object
  rio_readinitb(&m_fdbuf, fd);
}

Connection::~Connection() {
  // destructor, close the connection
    this->close();
}

bool Connection::is_open() const {
  if (m_last_result == EOF_OR_ERROR) {
    // if connnection closed, m_last_result should be error 
    return false;
  }
  return true;
}

void Connection::close() {
  // TODO: close the connection if it is open
  if (this->is_open()) {
    //sys call to close the file
    ::close(m_fd);
    m_fd = -1;
  }
}

bool Connection::send(const Message &msg) {
  // TODO: send a message
  // return true if successful, false if not
  // make sure that m_last_result is set appropriately
  // assert(m_last_result == SUCCESS);
  // assert(is_open());
  if (m_last_result == EOF_OR_ERROR) {
    return false;
  }
  string message = msg.concat_message();
  ssize_t s = rio_writen(m_fd, message.c_str(), message.length());
  if (s != (ssize_t)message.length()) {
    m_last_result = EOF_OR_ERROR;
    return false;
  }

  m_last_result = SUCCESS;
  return true;
}

bool Connection::receive(Message &msg) {
  // TODO: receive a message, storing its tag and data in msg
  // return true if successful, false if not
  // make sure that m_last_result is set appropriately
  // assert(m_last_result == SUCCESS);
  // assert(is_open());

   //create buffer with maximum length and null terminator
  if (m_last_result == EOF_OR_ERROR) {
    return false;
  }
  char buf[Message::MAX_LEN + 1];
  ssize_t s = rio_readlineb(&m_fdbuf, buf, Message::MAX_LEN);
  if (s < 1) {
    // read error, set the message tag to empty
    msg.tag = TAG_EMPTY;
    m_last_result = EOF_OR_ERROR;
    return false;
  }
  string message(buf);
  // dissect the mssage into tag and data based on colon position
  int colon_pos = message.find(":");
  msg.tag = message.substr(0, colon_pos);
  msg.data = message.substr(colon_pos + 1, message.length());

  // if : doesn't exist ==> invalid message
  if(colon_pos < 0) {
    m_last_result = INVALID_MSG;
    return false;
  }

  // if tag does not belong to any of the categories below, also inavlid
  if (msg.tag != TAG_ERR && msg.tag != TAG_OK && 
  msg.tag != TAG_SLOGIN && msg.tag != TAG_RLOGIN &&
  msg.tag != TAG_JOIN && msg.tag != TAG_LEAVE && msg.tag != TAG_SENDALL
  && msg.tag != TAG_QUIT && msg.tag != TAG_DELIVERY) {
    m_last_result = INVALID_MSG;
    return false;
  }
  
  m_last_result = SUCCESS;
  return true;
}
