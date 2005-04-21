function handles = AreaImage(handles)

%%% Reads the current module number, because this is needed to find
%%% the variable values that the user entered.
CurrentModule = handles.Current.CurrentModuleNumber;
CurrentModuleNum = str2double(CurrentModule);

%textVAR01 = What did you call the segmented objects ?
%defaultVAR01 = Cells
ObjectName = char(handles.Settings.VariableValues{CurrentModuleNum,1});

%%%VariableRevisionNumber = 01

%%% Retrieves the label matrix image that contains the segmented objects
fieldname = ['Segmented', ObjectName];

%%% Checks whether the image exists in the handles structure.
if isfield(handles.Pipeline, fieldname) == 0,
    error(['Image processing has been canceled. Prior to running the Area Image module, you must have previously run a module that generates an image with the objects identified.  You specified in the Area Image module that the primary objects were named ',ObjectName,' which should have produced an image in the handles structure called ', fieldname, '. The Area Image module cannot locate this image.']);
end
LabelMatrixImage = handles.Pipeline.(fieldname);

% Get areas
props = regionprops(LabelMatrixImage,'Area');
area  = cat(1,props.Area);

% Quantize areas
index1 = find(area < 100);
index3 = find(area > 225);
index2 = setdiff(1:length(area),[index1;index3]);
qarea = zeros(size(area));
qarea(index1) = 1;qarea(index2) = 2;qarea(index3) = 3;
qarea = [0;qarea];

% Generate area map
areamap = qarea(LabelMatrixImage+1);

% Display result
fieldname = ['FigureNumberForModule',CurrentModule];
ThisModuleFigureNumber = handles.Current.(fieldname);
figure(ThisModuleFigureNumber);
imagesc(areamap)




