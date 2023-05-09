# Development Log

## Status 26.03.2021

### Improvements
- Polynomial Refract/Reflect works. An important change in the
shader was the correct transformation of incoming and normal vectors to local coordinate space. The final normal for the refraction/reflection shader has to be transformed back to world coordinates.

### Next Work Topics
- (<span style="color:green">fixed</span>) Need to check LFT camera whether coordinate transforms will improve camera under rotation and translation.
	- Can now translate/rotate camera without apparent loss of rendering quality.
- (<span style="color:green">fixed</span>) Polynomial definition needs to be extended to:
	- type identifying polynomial with normalizing value equal to sensor width.
	- type identifying polynomial with fixed normalization width. This with has to be given as additional parameter.
- (<span style="color:green">fixed</span>) Once the poly camera is ready, implement the distortions of the various Athena cameras.

## Status 29.03.2021

### Improvements
- (<span style="color:red">update 30.03: that is not true in large environments :-(</span>) LFT camera can now also be translated and rotated without any apparent problems.
- Polynomial definition has been extended

### Next Work Topics
- Create new software release of Catharsys/AnyX with Athena Poly cameras.


## Status 30.03.2021

### Improvements
- Bug fixes and release preparations

## Longer Term Ideas

- Find approximation method for ZEMAX black box models.

---------------------------------------------------------------------
# ToDo

| Date | Resolved | Topic                                 |
| -----| ------ | ------------------------------------- |
|      |  (ok)  	| Export camera sets to JSON	          |
|      |  (ok)  	| export source information for cameras |
|      |  (ok)  	| Import camera sets from JSON   |
|  | (ok) 			| automatic creation of cameras from db if they do not exist  |
|  | (ok) 			| Enable copying of camera sets between blend files via append |
|  | (ok) 			| Implement creation of equirectangular cameras via AnyCam DB |
|  | (ok) 			| copy camera set |
| 10.05.21 |  		| Export camera set visualization parameters |
| 10.05.21 |  		| Implement orthographic camera |
|  |  | Enable option to move world, such that camera is at origin. |
|  |  | Enable ground truth rendering for poly & lft cameras via shader replacement in scene. |
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |


