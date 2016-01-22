"""
Factory class for the Stiefel manifold. Initiation requires the dimensions
n, p to be specified. Optional argument k allows the user to optimize over
the product of k Stiefels.

Elements are represented as n x p matrices (if k == 1), and as k x n x p
matrices if k > 1 (Note that this is different to manopt!).
"""
import numpy as np
from scipy.linalg import expm

from pymanopt.tools.multi import multiprod, multitransp, multisym
from pymanopt.manifolds.manifold import Manifold


class Stiefel(Manifold):
    def __init__(self, height, width, k = 1):
        # Check that n is greater than or equal to p
        if height < width or width < 1: raise ValueError("Need n >= p >= 1. "
            "Values supplied were n = %d and p = %d." % (height, width))
        if k < 1: raise ValueError("Need k >= 1. Value supplied was k = %d."
                % k)
        # Set the dimensions of the Stiefel
        self._n = height
        self._p = width
        self._k = k

        # Set dimension
        self._dim = self._k*(self._n*self._p - .5*self._p*(self._p+1))

        # Set the name
        if k == 1:
            self._name = "Stiefel manifold St(%d, %d)" % (self._n, self._p)
        elif k >= 2:
            self._name = "Product Stiefel manifold St(%d, %d)^%d" % (self._n,
                self._p, self._k)

    @property
    def dim(self):
        return self._dim

    @property
    def name(self):
        return self._name

    @property
    def typicaldist(self):
        return np.sqrt(self._p * self._k)

    def dist(self, X, Y):
        # Geodesic distance on the manifold
        raise NotImplementedError()

    def inner(self, X, G, H):
        # Inner product (Riemannian metric) on the tangent space
        # For the stiefel this is the Frobenius inner product.
        return np.tensordot(G,H, axes=G.ndim)

    def proj(self, X, U):
        if self._k == 1:
            # Project into the tangent space. Usually the same as egrad2rgrad
            UNew = U - np.dot(X, np.dot(X.T, U) + np.dot(U.T,X)) / 2
            return UNew

        UNew = U - multiprod(X, multiprod(multitransp(X), U) +
                multiprod(multitransp(U), X)) / 2
        return UNew

    egrad2rgrad = proj

    def ehess2rhess(self, X, egrad, ehess, H):
        # Convert Euclidean hessian into Riemannian hessian.
        XtG = multiprod(multitransp(X), egrad)
        symXtG = multisym(XtG)
        HsymXtG = multiprod(H, symXtG)
        return self.proj(X, ehess - HsymXtG)

    # Retract to the Stiefel using the qr decomposition of X + G.
    def retr(self, X, G):
        if self._k == 1:
            # Calculate 'thin' qr decomposition of X + G
            q, r = np.linalg.qr(X + G)
            # Unflip any flipped signs
            XNew = np.dot(q, np.diag(np.sign(np.sign(np.diag(r))+.5)))
        else:
            XNew = X + G
            for i in xrange(self._k):
                q, r = np.linalg.qr(Y[i])
                XNew[i] = np.dot(q, np.diag(np.sign(np.sign(np.diag(r))+.5)))
        return XNew

    def norm(self, X, G):
        # Norm on the tangent space of the Stiefel is simply the Euclidean
        # norm.
        return np.linalg.norm(G)

    # Generate random Stiefel point using qr of random normally distributed
    # matrix.
    def rand(self):
        if self._k == 1:
            X = np.random.randn(self._n,self._p)
            q, r = np.linalg.qr(X)
            return q

        X = np.zeros((self._k, self._n, self._p))
        for i in xrange(self._k):
            X[i], r = np.linalg.qr(np.random.randn(self._n, self._p))
        return X

    def randvec(self, X):
        if self._k == 1:
            U = np.random.randn(self._n, self._p)
        else:
            U = np.random.randn(self._k, self._n, self._p)
        U = self.proj(X, U)
        U = U / np.linalg.norm(U)
        return U

    def transp(self, x1, x2, d):
        return self.proj(x2, d)

    def log(self, X, Y):
        raise NotImplementedError

    def exp(self, X, U):
        # TODO: Simplify these expressions.
        if self._k ==1:
            Y = (np.bmat([X, U]).dot(expm(np.bmat([[X.T.dot(U), -U.T.dot(U)],
                 [np.eye(self._p) , X.T.dot(U)]]))).dot(np.bmat([[expm(-X.T.dot(U))],
                 [np.zeros((self._p,self._p))]])))
        else:
            Y = np.zeros(np.shape(X))
            for i in xrange(self._k):
                Y[i] = (np.bmat([X[i], U[i]]).dot(expm(np.bmat([[X[i].T.dot(U[i]), -U[i].T.dot(U[i])],
                        [np.eye(self._p) , X[i].T.dot(U[i])]]))).dot(np.bmat([[expm(-X[i].T.dot(U[i]))],
                        [np.zeros((self._p,self._p))]])))
        return Y
