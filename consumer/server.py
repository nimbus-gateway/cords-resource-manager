import asyncio
import websockets
import json
import logging

async def receive_file(websocket, path):
    # Initialize variables for the filename and to check if the file transfer is complete
    logging.info("CORDS ML Downloading Client Started..!!")
    filename_to_save = None
    complete = False

    # Continuously receive chunks of data until the transfer is complete
    while not complete:
        # Receive a chunk of data from the WebSocket connection
        data_received = await websocket.recv()
        # Convert received data to a Python dictionary from JSON format
        data_received = json.loads(data_received)
        
        # If this is the first chunk, extract the filename to save from the received data
        if filename_to_save is None:
            filename_to_save = data_received["filename"]
        
        # Check if this message is the final chunk
        if 'end' in data_received and data_received['end']:
            complete = True
            continue
        
        # Convert the content to bytes for appending to the file
        file_content = bytes(data_received["content"])

                
        # Open the file and append the chunk (using 'ab' to append binary data)
        with open(filename_to_save, 'ab') as file:
            file.write(file_content)

# Start the WebSocket server
start_server = websockets.serve(receive_file, '0.0.0.0', 8765)

# Run the event loop until the server is complete
asyncio.get_event_loop().run_until_complete(start_server)

# Run the event loop forever to keep the server running
asyncio.get_event_loop().run_forever()
