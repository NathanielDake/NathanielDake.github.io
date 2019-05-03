import numpy as np
import matplotlib.pyplot as plt
import theano
import theano.tensor as T

from Machine_Learning.hmm.utils import get_obj_s3, random_normalized

class HMM:
    def __init__(self, M):
        self.M = M

    def fit(self, X, learning_rate=0.001, max_iter=10, V=None, p_cost=1.0, print_period=10):
        """Train HMM model using stochastic gradient descent."""

        # Determine V, the vocabulary size
        if V is None:
            V = max(max(x) for x in X) + 1
        N = len(X)

        preSoftmaxPi0 = np.zeros(self.M) # initial state distribution
        preSoftmaxA0 = np.random.randn(self.M, self.M) # state transition matrix
        preSoftmaxB0 = np.random.randn(self.M, V) # output distribution

        thx, cost = self.set(preSoftmaxPi0, preSoftmaxA0, preSoftmaxB0)

        # This is a beauty of theano and it's computational graph. By defining a cost function,
        # which is representing p(x), the probability of a sequence, we can then find the gradient
        # of the cost with respect to our parameters (pi, A, B). The gradient updated rules are
        # applied as usual. Note, the reason that this is stochastic gradient descent is because
        # we are only looking at a single training example at a time.
        pi_update = self.preSoftmaxPi - learning_rate * T.grad(cost, self.preSoftmaxPi)
        A_update = self.preSoftmaxA - learning_rate * T.grad(cost, self.preSoftmaxA)
        B_update = self.preSoftmaxB - learning_rate * T.grad(cost, self.preSoftmaxB)

        updates = [
            (self.preSoftmaxPi, pi_update),
            (self.preSoftmaxA, A_update),
            (self.preSoftmaxB, B_update),
        ]

        train_op = theano.function(
            inputs=[thx],
            updates=updates,
            allow_input_downcast=True
        )

        costs = []
        for it in range(max_iter):
            for n in range(N):
                # Looping through all N training examples
                c = self.get_cost_multi(X, p_cost).sum()
                costs.append(c)
                train_op(X[n])

        plt.plot(costs)
        plt.xlabel("Iteration Number")
        plt.ylabel("Cost")
        plt.show()

    def get_cost(self, x):
        return self.cost_op(x)

    def get_cost_multi(self, X, p_cost=1.0):
        P = np.random.random(len(X))
        return np.array([self.get_cost(x) for x, p in zip(X, P) if p < p_cost])

    def log_likelihood(self, x):
        return - self.cost_op(x)

    def set(self, preSoftmaxPi, preSoftmaxA, preSoftmaxB):
        # Create theano shared variables
        self.preSoftmaxPi = theano.shared(preSoftmaxPi)
        self.preSoftmaxA = theano.shared(preSoftmaxA)
        self.preSoftmaxB = theano.shared(preSoftmaxB)

        pi = T.nnet.softmax(self.preSoftmaxPi).flatten()
        # softmax returns 1xD if input is a 1-D array of size D
        A = T.nnet.softmax(self.preSoftmaxA)
        B = T.nnet.softmax(self.preSoftmaxB)

        # Define input, a vector
        thx = T.ivector("thx")

        def recurrence_to_find_alpha(t, old_alpha, x):
            """Scaled version of updates for HMM. This is used to find the forward variable alpha.

                Args:
                    t:         Current time step, from pass in from scan:
                               sequences=T.arange(1, thx.shape[0])
                    old_alpha: Previously returned alpha, or on the first time step the initial value,
                               outputs_info=[pi *  B[:, thx[0]], None]
                    x:         thx, non_sequences (our actual set of observations)
            """
            alpha = old_alpha.dot(A) * B[:, x[t]]
            s = alpha.sum()
            return (alpha / s), s

        # alpha and scale, once returned, are both matrices with values at each time step
        [alpha, scale], _ = theano.scan(
            fn=recurrence_to_find_alpha,
            sequences=T.arange(1, thx.shape[0]),
            outputs_info=[pi *  B[:, thx[0]], None],    # Initial value of alpha
            n_steps=thx.shape[0] - 1,
            non_sequences=thx,
        )

        # scale is an array, and scale.prod() = p(x)
        # The property log(A) + log(B) = log(AB) can be used here to prevent underflow problem
        p_of_x = -T.log(scale).sum()      # Negative log likelihood
        cost = p_of_x

        self.cost_op = theano.function(
            inputs=[thx],
            outputs=cost,
            allow_input_downcast=True,
        )
        return thx, cost


def fit_coin(file_key):
    """Loads data and trains HMM."""

    X = []
    for line in get_obj_s3(file_key).read().decode("utf-8").strip().split(sep="\n"):
        x = [1 if e == "H" else 0 for e in line.rstrip()]
        X.append(x)

    # Instantiate object of class HMM with 2 hidden states (heads and tails)
    hmm = HMM(2)
    hmm.fit(X)
    L = hmm.get_cost_multi(X).sum()
    print("Log likelihood with fitted params: ", round(L, 3))

    # Try the true values
    pi = np.array([0.5, 0.5])
    A = np.array([
        [0.1, 0.9],
        [0.8, 0.2]
    ])
    B = np.array([
        [0.6, 0.4],
        [0.3, 0.7]
    ])
    hmm.set(pi, A, B)
    L = hmm.get_cost_multi(X).sum()
    print("Log Likelihood with true params: ", round(L, 3))


if __name__ == "__main__":
    key = "coin_data.txt"
    fit_coin(key)