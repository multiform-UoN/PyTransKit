import numpy as np
from scipy import interp

import matplotlib.pyplot as plt

from .base import BaseTransform
from ..utils import check_array, assert_equal_shape


class CDT(BaseTransform):
    """
    Cumulative Distribution Transform.

    Attributes
    -----------
    displacements_ : 1d array
        Displacements u.
    transport_map_ : 1d array
        Transport map f.

    References
    ----------
    [The cumulative distribution transform and linear pattern classification]
    (https://arxiv.org/abs/1507.05936)
    """
    def __init__(self):
        super(CDT, self).__init__()


    def forward(self, x0, sig0, x1, sig1, rm_edge=False):
        """
        Forward transform.

        Parameters
        ----------
        sig0 : 1d array
            Reference signal.
        sig1 : 1d array
            Signal to transform.

        Returns
        -------
        lot : 1d array
            CDT of input signal sig1.
        """
        # Check input arrays
        sig0 = check_array(sig0, ndim=1, dtype=[np.float64, np.float32],
                           force_strictly_positive=True)
        sig1 = check_array(sig1, ndim=1, dtype=[np.float64, np.float32],
                           force_strictly_positive=True)

        # Input signals must be the same size
        #assert_equal_shape(sig0, sig1, ['sig0', 'sig1'])

        self.sig0_ = sig0

        # Cumulative sums
        cum0 = np.cumsum(sig0)
        cum1 = np.cumsum(sig1)

        # x co-ordinates and interpolated y co-ordinates
        #x = np.arange(sig0.size)
        x = x1
        #y = np.linspace(0, 1, sig0.size)
        y = x0
        
        a = y[0]
        b = y[len(y)-1]
        ytilde = (y-a)/(b-a)
        
        y0 = interp(ytilde, cum0, x0)
        y1 = interp(ytilde, cum1, x)

        # Compute displacements: u = f(x)-x
        self.displacements_ = interp(y, y0, y1-y0)

        # Compute transport map: f = x - u
        self.transport_map_ = self.displacements_ - y

        # self.transport_map_ = interp(cum1, cum0, x)
        # self.displacements_ = x - self.transport_map_

        # CDT = (x - f) * sqrt(I0)
        cdt = self.displacements_ * np.sqrt(sig0)
        
        if rm_edge:
            cdt = np.delete(cdt, 0)
            cdt = np.delete(cdt, len(cdt)-1)
            
            y = np.delete(y, 0)
            y = np.delete(y, len(y)-1)
            
            self.transport_map_ = np.delete(self.transport_map_, 0)
            self.transport_map_ = np.delete(self.transport_map_, len(self.transport_map_)-1)
            
        transport_map = self.transport_map_

        self.x1 = x1
        self.x0 = y
        self.is_fitted = True

        return cdt, transport_map, self.x0


    def inverse(self):
        """
        Inverse transform.

        Returns
        -------
        sig1_recon : 1d array
            Reconstructed signal sig1.
        """
        self._check_is_fitted()
        return self.apply_inverse_map(self.transport_map_, self.sig0_)


    def apply_forward_map(self, transport_map, sig1):
        """
        Appy forward transport map.

        Parameters
        ----------
        transport_map : 1d array
            Forward transport map.
        sig1 : 1d array
            Signal to transform.

        Returns
        -------
        sig0_recon : 1d array
            Reconstructed reference signal sig0.
        """
        # Check inputs
        transport_map = check_array(transport_map, ndim=1,
                                    dtype=[np.float64, np.float32])
        sig1 = check_array(sig1, ndim=1, dtype=[np.float64, np.float32],
                           force_strictly_positive=True)
        assert_equal_shape(transport_map, sig1, ['transport_map', 'sig1'])

        # Reconstruct sig0
        x = np.arange(sig1.size)
        fprime = np.gradient(transport_map)
        sig0_recon = fprime * interp(transport_map, x, sig1)
        return sig0_recon


    def apply_inverse_map(self, transport_map, sig0):
        """
        Apply inverse transport map.

        Parameters
        ----------
        transport_map : 1d array
            Forward transport map. Inverse is computed in this function.
        sig0 : 1d array
            Reference signal.

        Returns
        -------
        sig1_recon : 1d array
            Reconstructed signal sig1.
        """
        # Check inputs
        transport_map = check_array(transport_map, ndim=1,
                                    dtype=[np.float64, np.float32])
        sig0 = check_array(sig0, ndim=1, dtype=[np.float64, np.float32],
                           force_strictly_positive=True)
        assert_equal_shape(transport_map, sig0, ['transport_map', 'sig0'])

        # Reconstruct sig1
        #x = np.arange(sig0.size)
        x = self.x1
        fprime = np.gradient(transport_map)
        sig1_recon = interp(x, transport_map, sig0/fprime)
        return sig1_recon
