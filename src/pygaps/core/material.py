"""Contains the material class."""

from pygaps.data import MATERIAL_LIST
from pygaps.utilities.exceptions import ParameterError


class Material():
    """
    An unified descriptor for an adsorbent material.

    Parameters
    ----------
    name : str
        The name of the material.

    Other Parameters
    ----------------
    density : float
        Material density.
    molar_mass : float
        Material molar mass.

    Notes
    -----
    The members of the properties are left at the discretion
    of the user. There are, however, some unique properties
    which can be set.

    """
    # special reserved parameters
    _reserved_params = [
        "name",
        "density",
        "molar_mass",
    ]

    def __init__(
        self,
        name: str,
        store: bool = False,
        **properties,
    ):
        """Instantiate by passing all the parameters."""
        # Material name
        self.name = name

        # Rest of material properties
        self.properties = properties

        # Store reference in internal list
        if store:
            if self not in MATERIAL_LIST:
                MATERIAL_LIST.append(self)

    def __repr__(self):
        """Print material id."""
        return f"<pygaps.Material '{self.name}'>"

    def __str__(self):
        """Print material standard name."""
        return self.name

    def __hash__(self):
        """Override hashing as a hash of name."""
        return hash(self.name)

    def __eq__(self, other):
        """Overload equality operator to use name."""
        if isinstance(other, Material):
            return self.name == other.name
        return self.name == other

    def __add__(self, other):
        """Overload addition operator to use name."""
        return self.name + other

    def __radd__(self, other):
        """Overload rev addition operator to use name."""
        return other + self.name

    def print_info(self):
        """Print a short summary of all the material parameters."""
        string = f"pyGAPS Material: '{self.name}'\n"

        if self.properties:
            string += "Other properties: \n"
            for prop, val in self.properties.items():
                string += (f"\t{prop}: {str(val)}\n")

        print(string)

    @classmethod
    def find(cls, name: str):
        """Get the specified material from the master list.

        Parameters
        ----------
        name : str
            The name of the material to search.

        Returns
        -------
        Material
            Instance of class.

        Raises
        ------
        ``ParameterError``
            If it does not exist in list.
        """
        # Skip search if already material
        if isinstance(name, Material):
            return name
        if not isinstance(name, str):
            raise ParameterError("Pass a string as an material name.")

        # Checks to see if material exists in master list
        try:
            return next(mat for mat in MATERIAL_LIST if name == mat)
        except StopIteration as err:
            raise ParameterError(
                f"Material {name} does not exist in list of materials. "
                "First populate pygaps.MATERIAL_LIST with required material class"
            ) from err

    def to_dict(self) -> dict:
        """
        Return a dictionary of the material class.

        Is the same dictionary that was used to create it.

        Returns
        -------
        dict
            Dictionary of all parameters.

        """
        parameters_dict = {'name': self.name}
        parameters_dict.update(self.properties)
        return parameters_dict

    @property
    def density(self) -> float:
        """Material density, in g/cm3 (optional)."""
        return self.properties.get("density")

    @density.setter
    def density(self, val: float):
        if val:
            self.properties["density"] = float(val)

    @property
    def molar_mass(self) -> float:
        """Material molar mass, in g/mol (optional)."""
        return self.properties.get("molar_mass")

    @molar_mass.setter
    def molar_mass(self, val: float):
        if val:
            self.properties["molar_mass"] = float(val)

    def get_prop(self, prop: str):
        """
        Return a property from the internal dictionary.

        Parameters
        ----------
        prop : str
            Property name desired.

        Returns
        -------
        str/float
            Value of property in the properties dict.

        Raises
        ------
        ``ParameterError``
            If it does not exist.

        """
        req_prop = self.properties.get(prop)
        if req_prop is None:
            try:
                req_prop = getattr(self, prop)
            except AttributeError as exc:
                raise ParameterError(
                    f"Material '{self.name}' does not have a property named '{prop}'."
                ) from exc

        return req_prop
