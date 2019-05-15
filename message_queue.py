from collections import deque

class Message:
    def __init__(self, content, **kwargs):
        """Create a new message.
        :param dict content: Content of the message
        :param dict kwargs: Extra parameters for the message
        """
        self._message = {}
        self._message['body'] = content
        self._message['properties'] = kwargs
    def get_content(self):
        """Get the message content.
        :return type: dict
        """
        return self._message
    def get_content_body(self):
    	return self._message['body']

class Publisher:
    def __init__(self, adapter):
        """Create a new publisher with an Adapter instance.
        :param BaseAdapter adapter: Connection Adapter
        """
        self.adapter = adapter

    def publish(self, message):
        """Publish a message message.
        :param Message message: Message to publish in the channel
        """
        self.adapter.send(message)

class Subscriber:
    def __init__(self, adapter):
        """Create a new subscriber with an Adapter instance.
        :param BaseAdapter adapter: Connection Adapter
        """
        self.adapter = adapter

    def consume(self):
        """Consume a queued message.
        :param function worker: Worker to execute when consuming the message
        """
        return self.adapter.consume()

global_message_queue = {}

class Adapter:
	def __init__(self, name):
		self.name = name
		if global_message_queue.get(self.name,None)==None:
			queue=deque()
			global_message_queue[self.name]=queue
		self.queue=global_message_queue[self.name]

	def consume(self):
		if self.queue:
			message = self.queue.popleft()
		else:
			message = None
		return message

	def send(self, message):
		self.queue.append(message)



