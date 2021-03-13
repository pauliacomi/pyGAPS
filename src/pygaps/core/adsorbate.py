"""Contains the adsorbate class."""

import warnings

from ..data import ADSORBATE_LIST
from ..utilities.converter_unit import _PRESSURE_UNITS
from ..utilities.converter_unit import c_unit
from ..utilities.coolprop_utilities import CP
from ..utilities.coolprop_utilities import thermodynamic_backend
from ..utilities.exceptions import CalculationError
from ..utilities.exceptions import ParameterError


class Adsorbate():
    """
    An unified class descriptor for an adsorbate.

    Its purpose is to expose properties such as adsorbate name,
    and formula, as well as physical properties, such as molar mass
    vapour pressure, etc.

    The properties can be either calculated through a wrapper over
    CoolProp or supplied in the initial adsorbate creation.
    All parameters passed are saved in a self.parameters
    dictionary.

    Parameters
    ----------
    name : str
        The name which should be used for this adsorbate.

    Other Parameters
    ----------------
    alias : list
        Other names the same adsorbate might take.
        Example: name=propanol, alias=['1-propanol'].
        pyGAPS disregards capitalisation (Propanol = propanol = PROPANOL).
    formula : str
        A chemical formula for the adsorbate in LaTeX form: He/N_{2}/C_{2}H_{4} etc.
    backend_name : str
        Used for integration with CoolProp/REFPROP. For a list of names
        look at the CoolProp `list of fluids
        <http://www.coolprop.org/fluid_properties/PurePseudoPure.html#list-of-fluids>`_
    molar_mass : float
        Custom value for molar mass (otherwise obtained through CoolProp).
    saturation_pressure : float
        Custom value for saturation pressure (otherwise obtained through CoolProp).
    surface_tension : float
        Custom value for surface tension (otherwise obtained through CoolProp).
    liquid_density : float
        Custom value for liquid density (otherwise obtained through CoolProp).
    liquid_molar_density : float
        Custom value for liquid molar density (otherwise obtained through CoolProp).
    gas_density : float
        Custom value for gas density (otherwise obtained through CoolProp).
    gas_molar_density : float
        Custom value for gas molar density (otherwise obtained through CoolProp).
    enthalpy_liquefaction : float
        Custom value for enthalpy of liquefaction (otherwise obtained through CoolProp).

    Notes
    -----
    The members of the properties dictionary are left at the discretion of the
    user, to keep the class extensible. There are, however, some unique
    properties which are used by calculations in other modules listed in the
    other parameters section above.

    These properties can be either calculated by CoolProp (if the adsorbate
    exists in CoolProp/REFPROP) or taken from the parameters dictionary. They
    are best accessed using the associated function.

    Calculated::

        my_adsorbate.surface_tension(77)

    Value from dictionary::

        my_adsorbate.surface_tension(77, calculate=False)

    If available, the underlying CoolProp state object
    (http://www.coolprop.org/coolprop/LowLevelAPI.html) can be accessed directly
    through the backend variable. For example, to get the CoolProp-calculated
    critical pressure::

        adsorbate.backend.p_critical()

    """
    def __init__(self, name: str = None, **properties):
        """Instantiate by passing a dictionary with the parameters."""
        # Adsorbate name
        if name is None:
            raise ParameterError(
                "Must provide a name for the created adsorbate."
            )
        self.name = name

        # List of aliases
        alias = properties.pop('alias', None)

        # Generate list of aliases
        _name = name.lower()
        if alias is None:
            self.alias = [_name]
        else:
            if isinstance(alias, str):
                self.alias = [alias.lower()]
            else:
                self.alias = [a.lower() for a in alias]
            if _name not in self.alias:
                self.alias.append(_name)

        #: Adsorbate properties
        self.properties = properties

        # CoolProp interaction variables, only generate when called
        self._state = None
        self._backend_mode = None

        # TODO
        # auto-upload adsorbates to global list?

    def __repr__(self):
        """Print adsorbate id."""
        return f"<pygaps.Adsorbate '{self.name}'>"

    def __str__(self):
        """Print adsorbate standard name."""
        return self.name

    def __hash__(self):
        """Override hashing as a name hash."""
        return hash(self.name)

    def __eq__(self, other):
        """Overload equality operator to include aliases."""
        if isinstance(other, Adsorbate):
            return self.name == other.name
        return other.lower() in self.alias

    def __add__(self, other):
        """Overload addition operator to use name."""
        return self.name + other

    def __radd__(self, other):
        """Overload rev addition operator to use name."""
        return other + self.name

    def print_info(self):
        """Print a short summary of all the adsorbate parameters."""
        string = ""

        string += f"Adsorbate: {self.name}\n"
        string += f"Aliases: { *self.alias,}\n"

        for prop in self.properties:
            string += f"{prop}:{str(self.properties.get(prop))}\n"

        return string

    @classmethod
    def find(cls, name: str):
        """Get the specified adsorbate from the master list.

        Parameters
        ----------
        name : str
            The name of the adsorbate to search

        Returns
        -------
        Adsorbate
            Instance of class

        Raises
        ------
        ``ParameterError``
            If it does not exist in list.
        """
        # Skip search if already adsorbate
        if isinstance(name, Adsorbate):
            return name
        elif not isinstance(name, str):
            raise ParameterError("Pass a string as an adsorbate name.")

        # See if adsorbate exists in master list
        try:
            return next(ads for ads in ADSORBATE_LIST if ads == name)
        except StopIteration:
            raise ParameterError(
                f"Adsorbate '{name}' does not exist in list of adsorbates. "
                "First populate pygaps.ADSORBATE_LIST with required adsorbate class."
            ) from None

    @property
    def backend(self):
        """Return the CoolProp state associated with the fluid."""
        if (
            not self._backend_mode
            or self._backend_mode != thermodynamic_backend()
        ):
            self._backend_mode = thermodynamic_backend()
            self._state = CP.AbstractState(
                self._backend_mode, self.backend_name
            )

        return self._state

    @property
    def formula(self) -> str:
        """Return the adsorbate formula."""
        formula = self.properties.get('formula')
        if formula is None:
            return self.name
        return formula

    def to_dict(self) -> dict:
        """
        Return a dictionary of the adsorbate class.

        Is the same dictionary that was used to create it.

        Returns
        -------
        dict
            dictionary of all parameters
        """
        parameters_dict = {
            'name': self.name,
            'alias': self.alias,
        }
        parameters_dict.update(self.properties)
        return parameters_dict

    def get_prop(self, prop):
        """
        Return a property from the 'properties' dictionary.

        Parameters
        ----------
        prop : str
            property name desired

        Returns
        -------
        str/float
            Value of property in the properties dict

        Raises
        ------
        ``ParameterError``
            If the the property does not exist
            in the class dictionary.
        """
        req_prop = self.properties.get(prop)
        if req_prop is None:
            raise ParameterError(
                f"Adsorbate '{self.name}' does not have a property named '{prop}'."
            )
        return req_prop

    @property
    def backend_name(self):
        """
        Get the CoolProp interaction name of the adsorbate.

        Returns
        -------
        str
            Value of backend_name in the properties dict

        Raises
        ------
        ``ParameterError``
            If the the property does not exist
            in the class dictionary.
        """
        c_name = self.properties.get("backend_name")
        if c_name is None:
            raise ParameterError(
                f"Adsorbate '{self.name}' does not have a property named "
                "backend_name. This must be available for CoolProp interaction."
            )
        return c_name

    def molar_mass(self, calculate=True):
        """
        Return the molar mass of the adsorbate.

        Parameters
        ----------
        calculate : bool, optional
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Molar mass in g/mol.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.
        """
        if calculate:
            try:
                return self.backend.molar_mass() * 1000

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                try:
                    return self.molar_mass(calculate=False)
                except ParameterError:
                    raise CalculationError

        return self.get_prop("molar_mass")

    def saturation_pressure(self, temp, unit=None, calculate=True):
        """
        Get the saturation pressure at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the pressure is desired in K.
        unit : str
            Unit in which to return the saturation pressure.
            If not specifies defaults to Pascal.
        calculate : bool, optional
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Pressure in unit requested.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self.backend
                state.update(CP.QT_INPUTS, 0.0, temp)
                sat_p = state.p()

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                try:
                    sat_p = self.saturation_pressure(
                        temp, unit=unit, calculate=False
                    )
                except ParameterError:
                    raise CalculationError

            if unit is not None:
                sat_p = c_unit(_PRESSURE_UNITS, sat_p, 'Pa', unit)
            return sat_p

        return self.get_prop("saturation_pressure")

    def surface_tension(self, temp, calculate=True):
        """
        Get the surface tension at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the surface_tension is desired in K.
        calculate : bool, optional
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Surface tension in mN/m.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self.backend
                state.update(CP.QT_INPUTS, 0.0, temp)
                return state.surface_tension() * 1000

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                try:
                    return self.surface_tension(temp, calculate=False)
                except ParameterError:
                    raise CalculationError

        return self.get_prop("surface_tension")

    def liquid_density(self, temp, calculate=True):
        """
        Get the liquid density at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the liquid density is desired in K.
        calculate : bool, optional.
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Liquid density in g/cm3.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self.backend
                state.update(CP.QT_INPUTS, 0.0, temp)
                return state.rhomass() / 1000

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                try:
                    return self.liquid_density(temp, calculate=False)
                except ParameterError:
                    raise CalculationError

        return self.get_prop("liquid_density")

    def liquid_molar_density(self, temp, calculate=True):
        """
        Get the liquid molar density at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the liquid density is desired in K.
        calculate : bool, optional.
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Molar liquid density in mol/cm3.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self.backend
                state.update(CP.QT_INPUTS, 0.0, temp)
                return state.rhomolar() / 1e6

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                try:
                    return self.liquid_molar_density(temp, calculate=False)
                except ParameterError:
                    raise CalculationError

        return self.get_prop("liquid_molar_density")

    def gas_density(self, temp, calculate=True):
        """
        Get the gas molar density at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the gas density is desired in K.
        calculate : bool, optional.
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Gas density in g/cm3.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self.backend
                state.update(CP.QT_INPUTS, 1.0, temp)
                return state.rhomass() / 1000

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                try:
                    return self.gas_density(temp, calculate=False)
                except ParameterError:
                    raise CalculationError

        return self.get_prop("gas_density")

    def gas_molar_density(self, temp, calculate=True):
        """
        Get the gas density at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the gas density is desired in K.
        calculate : bool, optional.
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Molar gas density in mol/cm3.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self.backend
                state.update(CP.QT_INPUTS, 1.0, temp)
                return state.rhomolar() / 1e6

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                try:
                    return self.gas_molar_density(temp, calculate=False)
                except ParameterError:
                    raise CalculationError

        return self.get_prop("gas_molar_density")

    def enthalpy_liquefaction(self, temp, calculate=True):
        """
        Get the enthalpy of liquefaction at a particular temperature.

        Parameters
        ----------
        temp : float
            Temperature at which the enthalpy of liquefaction is desired, in K.
        calculate : bool, optional
            Whether to calculate the property or look it up in the properties
            dictionary, default - True.

        Returns
        -------
        float
            Enthalpy of liquefaction in kJ/mol.

        Raises
        ------
        ``ParameterError``
            If the calculation is not requested and the property does not exist
            in the class dictionary.
        ``CalculationError``
            If it cannot be calculated, due to a physical reason.

        """
        if calculate:
            try:
                state = self.backend

                state.update(CP.QT_INPUTS, 0.0, temp)
                h_liq = state.hmolar()

                state.update(CP.QT_INPUTS, 1.0, temp)
                h_vap = state.hmolar()

                return (h_vap - h_liq) / 1000

            except Exception as e_info:
                warnings.warn(str(e_info))
                warnings.warn('Attempting to read dictionary')
                try:
                    return self.enthalpy_liquefaction(temp, calculate=False)
                except ParameterError:
                    raise CalculationError

        else:
            return self.get_prop("enthalpy_liquefaction")
