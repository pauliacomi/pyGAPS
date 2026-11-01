"""
Simple command-line interface for pyGAPS.

The main() function is defined as the entrypoint in setuptools' console_scripts.
"""

import argparse
import pathlib

SUPPORTED_SUFFIXES = ('.json', '.csv', '.xls', '.xlsx', '.aif')
CONVERSION_KEYS = (
    'pressure_mode',
    'pressure_unit',
    'loading_basis',
    'loading_unit',
    'material_basis',
    'material_unit',
)


def conversion_arguments(value):
    """Parse explicit conversion pairs without silently discarding input."""
    arguments = {}
    for pair in value.split(','):
        if pair.count('=') != 1:
            raise argparse.ArgumentTypeError('Conversions must be comma-separated key=value pairs.')
        key, setting = (part.strip() for part in pair.split('='))
        if key not in CONVERSION_KEYS:
            raise argparse.ArgumentTypeError(f"Unknown conversion key '{key}'.")
        if not setting:
            raise argparse.ArgumentTypeError(f"Conversion value for '{key}' cannot be empty.")
        if key in arguments:
            raise argparse.ArgumentTypeError(f"Duplicate conversion key '{key}'.")
        arguments[key] = setting
    return arguments


def main(argv=None):
    """
    Run the main entrypoint for the cli.

    Currently the CLI can read any pyGAPS format (JSON, CSV, Excel) and then:

    * print isotherm to output (default if no argument is passed)
    * plot the isotherm using a Matplotlib window (``-p/--plot``)
    * run basic automated characterization tests (``-ch/--characterize a_bet``
      for the BET area for example)
    * attempt to model the isotherm using a requested model or guess the best
      fitting model (``-md/--model guess``) and save the resulting isotherm
      model using the ``-o/--outfile`` path.
    * convert the isotherm to any unit/basis
      (``-cv/--convert pressure_mode=absolute,pressure_unit=bar``) and save the
      resulting isotherm model using the ``-o/--outfile`` path.

    Parameters
    ----------
    argv : list[str], optional
        Arguments to parse, excluding the executable name. If omitted, use
        the process command line.

    """
    # Create the parser
    prs = argparse.ArgumentParser(prog='pygaps', description='Command-line interface to pyGAPS')

    # Add the arguments
    prs.add_argument(
        'iso',
        metavar='isotherm',
        nargs='?',
        type=pathlib.Path,
        help='isotherm to display or process',
    )
    actions = prs.add_mutually_exclusive_group()
    actions.add_argument(
        '-p',
        '--plot',
        action='store_true',
        help='plot the isotherm',
    )
    actions.add_argument(
        '-ch',
        '--characterize',
        help='run characterization methods (BET area, PSD, etc).',
        choices=['a_bet', 'a_lang', 'kh'],
    )
    actions.add_argument(
        '-md',
        '--model',
        choices=['guess', 'henry', 'langmuir', 'dslangmuir', 'bet'],
        help='model an isotherm, saved as the file specified at \'-o\'',
    )
    actions.add_argument(
        '-cv',
        '--convert',
        type=conversion_arguments,
        help='convert to another unit/basis, savepath using \'-o\'',
    )
    prs.add_argument(
        '-o',
        '--outfile',
        type=pathlib.Path,
        help='output path for a resulting isotherm',
    )
    prs.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='increase verbosity',
    )
    prs.add_argument(
        '-V',
        '--version',
        action="store_true",
        help="Print current version.",
    )

    # Execute the parse_args() method
    args = prs.parse_args(argv)

    if args.version:
        from importlib.metadata import version

        print(version("pygaps"))
        return

    # Read the isotherm
    if not args.iso:
        prs.print_help()
        return

    if not args.iso.is_file():
        prs.error(f"Input file does not exist or is not a file: {args.iso}")
    if args.iso.suffix not in SUPPORTED_SUFFIXES:
        prs.error(f"Cannot read '{args.iso.suffix}' files.")
    if args.outfile and (args.model or args.convert) and args.outfile.suffix not in SUPPORTED_SUFFIXES:
        prs.error(f"Cannot export as '{args.outfile.suffix}' files.")

    import pygaps.parsing as pgp

    ext = args.iso.suffix
    if ext == '.json':
        iso = pgp.isotherm_from_json(args.iso)
    elif ext == '.csv':
        iso = pgp.isotherm_from_csv(args.iso)
    elif ext in ('.xls', '.xlsx'):
        iso = pgp.isotherm_from_xl(args.iso)
    else:
        iso = pgp.isotherm_from_aif(args.iso)

    from pygaps import ModelIsotherm
    from pygaps import PointIsotherm

    plot = False
    out_iso = None

    # pass to various characterization functions
    if args.characterize:
        if not isinstance(iso, (PointIsotherm, ModelIsotherm)):
            prs.error('Characterization requires point or model isotherm data.')
        import pygaps.characterisation as pgc

        plot = args.verbose
        if args.characterize == 'a_bet':
            res = pgc.area_BET(iso, verbose=args.verbose)
        elif args.characterize == 'a_lang':
            res = pgc.area_langmuir(iso, verbose=args.verbose)
        else:
            res = pgc.initial_henry_slope(iso, verbose=args.verbose)
        print(res)

    # model isotherm using `model_iso`
    elif args.model:
        if not isinstance(iso, PointIsotherm):
            prs.error('Model fitting requires point isotherm data.')
        import pygaps.modelling as pgm

        plot = args.verbose
        out_iso = pgm.model_iso(iso, model=args.model, verbose=args.verbose)

    # convert an isotherm to a different basis/unit
    elif args.convert:
        if not isinstance(iso, PointIsotherm):
            prs.error('Conversion requires point isotherm data.')
        from pygaps.utilities.exceptions import CalculationError
        from pygaps.utilities.exceptions import ParameterError

        try:
            iso.convert(**args.convert, verbose=args.verbose)
        except ParameterError as error:
            prs.error(str(error))
        except CalculationError as error:
            # Pressure conversion wraps invalid units/modes, but scientific failures must remain visible.
            if isinstance(error.__cause__, ParameterError):
                prs.error(str(error.__cause__))
            raise
        out_iso = iso

    # simply plot the isotherm
    elif args.plot:
        if not isinstance(iso, (PointIsotherm, ModelIsotherm)):
            prs.error('Plotting requires point or model isotherm data.')
        iso.plot()
        plot = True

    # default to printing isotherm to stdout
    else:
        print(iso)

    if out_iso:
        if args.outfile:
            ext = args.outfile.suffix
            if ext == '.json':
                out_iso.to_json(args.outfile)
            elif ext == '.csv':
                out_iso.to_csv(args.outfile)
            elif ext in ('.xls', '.xlsx'):
                out_iso.to_xl(args.outfile)
            elif ext == '.aif':
                out_iso.to_aif(args.outfile)

        if args.verbose:
            print(out_iso)

    if plot:
        import matplotlib.pyplot as plt

        plt.show()
