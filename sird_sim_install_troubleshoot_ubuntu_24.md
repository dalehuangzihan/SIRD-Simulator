# SIRD-Simulator install problems

## Installing ns-2.34 from source:

1. ns2.34/otcl and ns2.34/tclcl simlinks are empty.
	a. Remedy by copying otcl-1.13 and tclcl-1.19 directories from ns-allinone-2.34 into ns2.34/
	
1. ns2.34/ns-2.34/indep-utils/cmu-scen-gen/setdest was not present in SIRD repo.
	a. Remedy by copying relevant directory from ns-allinone-2.34
	
1. ns-2.34/diffusion3/ns/ directory was absent from SIRD repo; can be found in ns-allinone-2.34

1. ns-2.34/bin/ directory was absent from SIRD repo (might be cuz build failed...?); can be found in ns-allinone-2.34 (after we try to run ./install ...?)
