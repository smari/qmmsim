# QMM Simulator

QMM, or the Quarterly Macroeconomic Model of the Icelandic Economy, is a model written in the Abaqus language, and supplemented with data from a published Excel file, which underlies the Icelandic Central Bank's economic analysis.

Whereas Abaqus is non-free software and the model, which is quite complex, provides relatively little possibility to perform arbitrary analysis without this specialized software, this is a small project that tries to create a simulation under which the model can be analyzed.

## Getting started

In order for this to work, you need to fetch the QMM model files from [the Icelandic Central Bank Website](http://www.sedlabanki.is/peningastefna/efnahagsspa/). Put the files in appropriate places (`sedlabanki/`) with appropriate names (see `main.py`).

Also, install the requirements: `pip install requirements.txt`

Finally, just run it: `python main.py`

... and very little will happen, in fact.

## About QMM

The QMM model is developed and published by Seðlabanki Íslands, the Icelandic Central Bank. It is available for download [on their website](http://www.sedlabanki.is/peningastefna/efnahagsspa/).

The model itself consists of two files in Abaqus format: "Líkanaskrá", which contains the actual model, and "Stikaskrá", which contains various initial coefficients. In addition, there is a Microsoft Excel file, referred to quaintly as a "database", which contains time series data.

There are three data types in the model.

First, there are scalar values used as coefficients, which are declared as "COEFFICIENTS" in the model. These are given values by the coefficient file.

Secondly, there are "EXOGENOUS" time series. These are obtained from the Excel "database".

Third, there are "ENDOGENOUS" time series, which are calculated at each moment in time (the model works on the granularity of quarters; hence the name) with respect to each other. These are specified in the model file.

## Development approach

The first thought was to simply translate each statement in the model to Python, but this would have been a less-than-optimal idea, whereas it would lead to divergence if and when the Central Bank releases a new version of the model files.

Instead, because the Abaqus language is fairly simple and the declarations easy to extract from the files, it's more natural to simply parse the files and use the declarations to populate a simulation data structure, which can then be manipulated.

Currently, this is a fairly messy mish-mash, due to exploratory coding. Needs cleanup!

The next thing to do is to change the parser so that it populates a tree structure. For instance, if we had the following Abaqus file:
```
ADDSYM
COEFFICIENT PI,
ENDOGENOUS FIB Floop,
EXOGENOUS OneToTen,
;

PI = 3.14159265,
FIB: FIB = FIB(-1) + FIB(-2),
Floop: Floop = FIB + (OneToTen*PI),
;
```

Then we could end up with a tree like this:
```
  [root]--+
          |-- [ENDO] FIB = FIB(-1) + FIB(-2)
          |    |- Decl(FIB)
          |       |- Sum
          |          |- Ref(FIB, -1)
          |          |- Ref(FIB, -2)
          |-- [EXOG] OneToTen = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
          |    |- Decl(OneToTen)
          |       |- Data (...)
          |-- [COEF] PI = 3.14159265
          |    |- Decl(PI)
          |       |- Constant(3.14159265)
          |-- [ENDO] Floop = FIB + OneToTen*PI
               |- Decl(Floop)
                  |- Sum
                     |- Ref(FIB)
                     |- Mul
                        |- Ref(OneToTen)
                        |- Ref(PI)
```

This tree could then be evaluated as needed.

## TODO

 * [ ] Allow loading data from multiple data sources (#NiceToHave)
 * [ ] Think about coherent structure for error reporting
 * [X] Make internal tree structure for expressions
 * [X] Allow for lazy/non-blocking evaluation of statements
 * [X] Make evaluator that resolves equations at certain time indexes
 * [ ] Guarantee that evaluator doesn't recurse infinitely
 * [ ] Make something that shows the values over time (#Graphics)

## Author

 * Smári McCarthy <smari@smarimccarthy.is>
