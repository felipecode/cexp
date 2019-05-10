from cexp.env.server_manager import ServerManagerDocker, find_free_port
import carla

def start_test_server(port=6666, gpu=0 ,docker_name='carlalatest:latest'):

    params = {
              'docker_name': docker_name,
              'gpu': gpu
              }

    docker_server = ServerManagerDocker(params)
    docker_server.reset(port=port)



def check_test_server(port):

    # Check if a server is open at some port

    try:
        client = carla.Client(host='localhost', port=port)
        client.get_server_version()
        return True
    except:
        return False