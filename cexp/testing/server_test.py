from cexp.env.server_manager import ServerManagerDocker, find_free_port
import carla

def start_test_server(port=6666):

    docker_server = ServerManagerDocker()
    docker_server.reset(port=port)



def check_test_server(port):

    # Check if a server is open at some port

    try:
        _ = carla.Client(host='localhost', port=port)
        return True
    except:
        return False