import traceback
from cexp.cexp import CEXP


def main_cex(json_file, params, number_iterations, agent, sequential, debug):

    # THe experience is built, the files necessary
    env_batch = CEXP(json_file, params, number_iterations,
                     params['batch_size'], sequential=sequential, debug=debug)


    # to load CARLA and the scenarios are made
    # Here some docker was set
    env_batch.start()

    for env in env_batch:

        try:
            states, rewards = agent.unroll(env)
            agent.reinforce(rewards)
            # if the agent is already un
            summary = env.get_summary()

        except KeyboardInterrupt:
            env.stop()
            break
        except:
            traceback.print_exc()
            # Just try again
            env.stop()
            print (" ENVIRONMENT BROKE trying again.")



if __name__ == '__main__':

    pass