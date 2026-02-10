import numpy as np
import tensorflow as tf

np.random.seed(1)
tf.random.set_seed(1)


class QNetwork(tf.keras.Model):  
    def __init__(self, n_features, n_actions):
        super(QNetwork, self).__init__()
        self.l1 = tf.keras.layers.Dense(
            20, activation='relu',
            kernel_initializer=tf.random_normal_initializer(0., 0.3),
            bias_initializer=tf.constant_initializer(0.1)
        )
        self.l2 = tf.keras.layers.Dense(
            n_actions,
            kernel_initializer=tf.random_normal_initializer(0., 0.3),
            bias_initializer=tf.constant_initializer(0.1)
        )

    def call(self, x):
        x = self.l1(x)
        return self.l2(x)


class DoubleDQN:
    def __init__(
        self,
        n_actions,
        n_features,
        learning_rate=0.005,
        reward_decay=0.9,
        e_greedy=0.9,
        replace_target_iter=200,
        memory_size=3000,
        batch_size=32,
        e_greedy_increment=None,
    ):
        self.n_actions = n_actions
        self.n_features = n_features
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon_max = e_greedy
        self.replace_target_iter = replace_target_iter
        self.memory_size = memory_size
        self.batch_size = batch_size
        self.epsilon_increment = e_greedy_increment
        self.epsilon = 0 if e_greedy_increment is not None else self.epsilon_max

        self.learn_step_counter = 0
        self.memory = np.zeros((memory_size, n_features * 2 + 2))

        # Networks
        self.eval_net = QNetwork(n_features, n_actions)
        self.target_net = QNetwork(n_features, n_actions)

        # Initialize weights
        dummy = tf.zeros((1, n_features))
        self.eval_net(dummy)
        self.target_net(dummy)
        self.target_net.set_weights(self.eval_net.get_weights())

        self.optimizer = tf.keras.optimizers.Adam(self.lr)
        self.loss_fn = tf.keras.losses.MeanSquaredError()

        self.cost_his = []

    def store_transition(self, s, a, r, s_):
        if not hasattr(self, 'memory_counter'):
            self.memory_counter = 0
        transition = np.hstack((s, [a, r], s_))
        index = self.memory_counter % self.memory_size
        self.memory[index, :] = transition
        self.memory_counter += 1

    def choose_action(self, observation):
        observation = observation[np.newaxis, :]
        q_values = self.eval_net(observation).numpy()
        action = np.argmax(q_values)

        if np.random.uniform() > self.epsilon:
            action = np.random.randint(0, self.n_actions)
        return action

    def learn(self):
        if self.learn_step_counter % self.replace_target_iter == 0:
            self.target_net.set_weights(self.eval_net.get_weights())
            print('\ntarget_params_replaced\n')

        if self.memory_counter > self.memory_size:
            sample_index = np.random.choice(self.memory_size, self.batch_size)
        else:
            sample_index = np.random.choice(self.memory_counter, self.batch_size)

        batch = self.memory[sample_index, :]

        s = batch[:, :self.n_features]
        a = batch[:, self.n_features].astype(int)
        r = batch[:, self.n_features + 1]
        s_ = batch[:, -self.n_features:]

        q_eval = self.eval_net(s).numpy()
        q_next = self.target_net(s_).numpy()
        q_eval4next = self.eval_net(s_).numpy()

        q_target = q_eval.copy()
        batch_index = np.arange(self.batch_size)

        max_act4next = np.argmax(q_eval4next, axis=1) 
        selected_q_next = q_next[batch_index, max_act4next] 

        q_target[batch_index, a] = r + self.gamma * selected_q_next

        with tf.GradientTape() as tape:
            q_pred = self.eval_net(s)
            loss = self.loss_fn(q_target, q_pred)

        grads = tape.gradient(loss, self.eval_net.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.eval_net.trainable_variables))

        self.cost_his.append(loss.numpy())

        if self.epsilon_increment is not None:
            self.epsilon = min(self.epsilon + self.epsilon_increment, self.epsilon_max)

        self.learn_step_counter += 1