#include "guard.h"
#include "message.h"
#include "message_queue.h"
#include "user.h"
#include "room.h"
#include "client_util.h"

Room::Room(const std::string &room_name)
  : room_name(room_name) {
    pthread_mutex_init(&lock, NULL);
  // TODO: initialize the mutex
}

Room::~Room() {
  pthread_mutex_destroy(&lock);
  // TODO: destroy the mutex
  //free users
  for(std::set<User *>::iterator it = members.begin(); it!=members.end(); ++it){
    delete *it;
  }
}

void Room::add_member(User *user) {
  // TODO: add User to the room
  Guard g(lock);
  members.insert(user);
}

void Room::remove_member(User *user) {
  // TODO: remove User from the room
  Guard g(lock);
  members.erase(user);
}

void Room::broadcast_message(const std::string &sender_username, const std::string &message_text) {
  // TODO: send a message to every (receiver) User in the room
  Guard g(lock);
  std::string message_to_send = room_name + ":" + sender_username + ":" + message_text;
  for (UserSet::iterator it = members.begin(); it!=members.end(); ++it) {
    Message* to_send = new Message(TAG_DELIVERY, message_to_send);
    (*it)->mqueue.enqueue(to_send);
  }
}
