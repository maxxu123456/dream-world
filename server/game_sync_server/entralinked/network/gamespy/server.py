#!/usr/bin/env python3
import logging
import socketserver
import threading

from network.gamespy.handler import GameSpyHandler

logger = logging.getLogger(__name__)

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

class GameSpyServer:
    def __init__(self, context, port: int = 29900):
        self.context = context
        
        self.user_manager = self.context.user_manager
        self.port = port
        self.server: ThreadedTCPServer = None
        self.server_thread: threading.Thread = None

    def start(self):
        logger.info(f"Starting GameSpy TCP Server on port {self.port}...")
        
        self.server = ThreadedTCPServer(("0.0.0.0", self.port), GameSpyHandler)

        self.server.context = self.context

        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        
        logger.info("GameSpy server started successfully.")

    def stop(self):
        if self.server:
            logger.info("Shutting down GameSpy server...")
            self.server.shutdown()
            self.server.server_close()
            
            if self.server_thread:
                self.server_thread.join()
                
            logger.info("GameSpy server stopped.")
