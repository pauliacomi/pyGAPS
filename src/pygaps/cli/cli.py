"""
Simple command-line interface for pyGAPS.

The main() function is defined as the entrypoint in setuptools' console_scripts.
"""
import argparse
import pathlib


def main():
    """
    The main entrypoint for the cli.

    Currently the CLI can read any pyGAPS format (JSON, CSV, Excel) and then:

        * print isotherm to output (default if no argument is passed)
        * plot the isotherm using a Matplotlib window (``-p/--plot``)
        * run basic automated characterization tests (``-ch/--characterize a_bet``
          for the BET area for example)
        * attempt to model the isotherm using a requested model or guess the best
          fitting model (``-md/--model guess``) and save the resulting isotherm model
          using the ``-o/--outfile`` path.
        * convert the isotherm to any unit/basis
          (``-cv/--convert pressure_mode=absolute,pressure_unit=bar``) and save the
          resulting isotherm model using the ``-o/--outfile`` path.

    """

    # Create the parser
    prs = argparse.ArgumentParser(
        description='Command-line interface to pyGAPS'
    )

    # Add the arguments
    prs.add_argument(
        'iso',
        metavar='isotherm',
        type=pathlib.Path,
        help='isotherm to display or process',
    )
    prs.add_argument(
        '-p',
        '--plot',
        action='store_true',
        help='plot the isotherm',
    )
    prs.add_argument(
        '-ch',
        '--characterize',
        help='run characterization methods (BET area, PSD, etc).',
        choices=['a_bet', 'a_lang', 'kh'],
    )
    prs.add_argument(
        '-md',
        '--model',
        choices=['guess', 'henry', 'langmuir', 'dslangmuir', 'bet'],
        help='model an isotherm, saved as the file specified at \'-o\'',
    )
    prs.add_argument(
        '-cv',
        '--convert',
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

    # Execute the parse_args() method
    args = prs.parse_args()

    import pygaps as pg

    # Read the isotherm
    if not args.iso.exists():
        raise FileNotFoundError("Path does not exist.")

    ext = args.iso.suffix
    if ext == '.json':
        iso = pg.isotherm_from_json(args.iso)
    elif ext == '.csv':
        iso = pg.isotherm_from_csv(args.iso)
    elif ext == '.xls':
        iso = pg.isotherm_from_xl(args.iso)
    elif ext == '.aif':
        iso = pg.isotherm_from_aif(args.iso)
    else:
        from pygaps.utilities.exceptions import ParsingError
        raise ParsingError(f"Cannot read '{ext}' files")

    plot = False
    out_iso = None

    # pass to various characterization functions
    if args.characterize:
        plot = args.verbose
        if args.characterize == 'a_bet':
            res = pg.area_BET(iso, verbose=args.verbose)
            print(res)
        elif args.characterize == 'a_lang':
            res = pg.area_langmuir(iso, verbose=args.verbose)
        elif args.characterize == 'kh':
            res = pg.initial_henry_slope(iso, verbose=args.verbose)

    # model isotherm using `model_iso`
    elif args.model:
        plot = args.verbose
        out_iso = pg.model_iso(iso, model=args.model, verbose=args.verbose)

    # convert an isotherm to a different basis/unit
    elif args.convert:
        convert_args = {
            keyval.split('=')[0]: keyval.split('=')[1]
            for keyval in map(str.strip, args.convert.split(','))
        }
        convert_args['verbose'] = args.verbose
        iso.convert(**convert_args)
        out_iso = iso

    # simply plot the isotherm
    elif args.plot:
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
            elif ext == '.xls':
                out_iso.to_xl(args.outfile)
            elif ext == '.aif':
                out_iso.to_aif(args.outfile)
            else:
                from pygaps.utilities.exceptions import ParsingError
                raise ParsingError(f"Cannot export as '{ext}' files")

        if args.verbose:
            print(out_iso)

    if plot:
        import matplotlib.pyplot as plt
        plt.show()
