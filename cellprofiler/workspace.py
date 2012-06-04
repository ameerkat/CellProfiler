"""workspace.py - the workspace for an imageset

CellProfiler is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Copyright (c) 2003-2009 Massachusetts Institute of Technology
Copyright (c) 2009-2012 Broad Institute
All rights reserved.

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
"""
__version__="$Revision$"

from cellprofiler.cpgridinfo import CPGridInfo
from .utilities.hdf5_dict import HDF5FileList

'''Continue to run the pipeline

Set workspace.disposition to DISPOSITION_CONTINUE to go to the next module.
This is the default.
'''
DISPOSITION_CONTINUE = "Continue"
'''Skip remaining modules

Set workspace.disposition to DISPOSITION_SKIP to skip to the next image set
in the pipeline.
'''
DISPOSITION_SKIP = "Skip"
'''Pause and let the UI run

Set workspace.disposition to DISPOSITION_PAUSE to pause the UI. Set
it back to DISPOSITION_CONTINUE to resume.
'''
DISPOSITION_PAUSE = "Pause"
'''Cancel running the pipeline'''
DISPOSITION_CANCEL = "Cancel"

class Workspace(object):
    """The workspace contains the processing information and state for
    a pipeline run on an image set
    """
    def __init__(self,
                 pipeline,
                 module,
                 image_set,
                 object_set,
                 measurements,
                 image_set_list,
                 frame=None,
                 create_new_window = False,
                 outlines = {}):
        """Workspace constructor
        
        pipeline          - the pipeline of modules being run
        module            - the current module to run (a CPModule instance)
        image_set         - the set of images available for this iteration
                            (a cpimage.ImageSet instance)
        object_set        - an object.ObjectSet instance
        image_set_list    - the list of all images
        frame             - the application's frame, or None for no display
        create_new_window - True to create another frame, even if one is open
                            False to reuse the current frame.
        """
        self.__pipeline = pipeline
        self.__module = module
        self.__image_set = image_set
        self.__object_set = object_set
        self.__measurements = measurements
        self.__image_set_list = image_set_list
        self.__frame = frame
        self.__do_show = frame is not None
        self.__outlines = outlines
        self.__windows_used = []
        self.__create_new_window = create_new_window
        self.__grid = {}
        self.__disposition = DISPOSITION_CONTINUE
        self.__disposition_listeners = []
        self.__in_background = False # controls checks for calls to create_or_find_figure()
        self.__file_list = (None if measurements is None 
                            else HDF5FileList(measurements.hdf5_dict.hdf5_file))

        self.interaction_handler = None

        class DisplayData(object):
            pass
        self.display_data = DisplayData()
        """Object into which the module's run() method can stuff items
        that must be available later for display()."""
    
    def refresh(self):
        """Refresh any windows created during use"""
        for window in self.__windows_used:
            window.figure.canvas.draw()
    
    def get_windows_used(self):
        return self.__windows_used

    def get_pipeline(self):
        """Get the pipeline being run"""
        return self.__pipeline
    pipeline = property(get_pipeline)
    
    def get_image_set(self):
        """The image set is the set of images currently being processed
        """
        return self.__image_set
    
    def set_image_set_for_testing_only(self, image_set_number):
        self.__image_set = self.image_set_list.get_image_set(image_set_number)
        
    image_set = property(get_image_set)
    
    def get_image_set_list(self):
        """The list of all image sets"""
        return self.__image_set_list
    image_set_list = property(get_image_set_list)

    def get_object_set(self):
        """The object set is the set of image labels for the current image set
        """
        return self.__object_set
    
    object_set = property(get_object_set)

    def get_objects(self,objects_name):
        """Return the objects.Objects instance for the given name.
        
        objects_name - the name of the objects to retrieve
        """
        return self.object_set.get_objects(objects_name)

    def get_measurements(self):
        """The measurements contain measurements made on images and objects
        """
        return self.__measurements

    measurements = property(get_measurements)
    
    def add_measurement(self, object_name, feature_name, data):
        """Add a measurement to the workspace's measurements
        
        object_name - name of the objects measured or 'Image'
        feature_name - name of the feature measured
        data - the result of the measurement
        """
        self.measurements.add_measurement(object_name, feature_name, data)
        
    def get_file_list(self):
        '''The user-curated list of files'''
        return self.__file_list
    
    def set_file_list(self, file_list):
        """Set the file list
        
        A caller can set the file list to the file list in some other
        workspace. This lets a single, sometimes very bulky file list be
        used without copying it to a measurements file.
        """
        self.__file_list = file_list
    
    file_list = property(get_file_list)

    def get_grid(self, grid_name):
        '''Return a grid with the given name'''
        if not self.__grid.has_key(grid_name):
            raise ValueError("Could not find grid %s"%grid_name)
        return self.__grid[grid_name]
    
    def set_grids(self, last = None):
        '''Initialize the grids for an image set
        
        last - none if first in image set or the return value from
               this method.
        returns a grid dictionary
        '''
        if last is None:
            last = {}
        self.__grid = last
        return self.__grid
    
    def set_grid(self, grid_name, grid_info):
        '''Add a grid to the workspace'''
        self.__grid[grid_name] = grid_info
        
    def get_frame(self):
        """The frame is CellProfiler's gui window

        If the frame is present, a module should do its display
        """
        if self.__do_show:
            return self.__frame
        return None

    frame = property(get_frame)
    
    def show_frame(self, do_show):
        self.__do_show = do_show
    
    def get_display(self):
        """True to provide a gui display"""
        return self.__frame != None
    display = property(get_display)
    
    def get_in_background(self):
        return self.__in_background
    def set_in_background(self, val):
        self.__in_background = val
    in_background = property(get_in_background, set_in_background)

    def create_or_find_figure(self,title=None,subplots=None,window_name = None):
        """Create a matplotlib figure window or find one already created"""
        import cellprofiler.gui.cpfigure as cpf

        # catch any background threads trying to call display functions.
        assert not self.__in_background 

        if title==None:
            title=self.__module.module_name
            
        if window_name == None:
            window_name = cpf.window_name(self.__module)
            
        if self.__create_new_window:
            figure = cpf.CPFigureFrame(self, 
                                   title=title,
                                   name = window_name,
                                   subplots = subplots)
        else:
            figure = cpf.create_or_find(self.__frame, title = title, 
                                        name = window_name, 
                                        subplots = subplots)
        if not figure in self.__windows_used:
            self.__windows_used.append(figure)
        return figure
    
    def get_outline_names(self):
        """The names of outlines of objects"""
        return self.__outlines.keys()
    
    def add_outline(self, name, outline):
        """Add an object outline to the workspace"""
        self.__outlines[name] = outline
    
    def get_outline(self, name):
        """Get a named outline"""
        return self.__outlines[name]
    
    def get_module(self):
        """Get the module currently being run"""
        return self.__module
    
    module = property(get_module)
    
    def set_module(self, module):
        """Set the module currently being run"""
        self.__module = module
    
    def interaction_request(self, module, *args, **kwargs):
        '''make a request for GUI interaction via a pipeline event'''
        # See also:
        # main().interaction_handler() in analysis_worker.py
        # PipelineController.module_interaction_request() in pipelinecontroller.py
        import cellprofiler.preferences as cpprefs
        if self.interaction_handler is None:
            if cpprefs.get_headless():
                raise self.NoInteractionException()
            else:
                return module.handle_interaction(*args, **kwargs)
        else:
            return self.interaction_handler(module, *args, **kwargs)

    @property
    def is_last_image_set(self):
        return (self.measurements.image_set_number ==
                self.image_set_list.count()-1)
    
    def get_disposition(self):
        '''How to proceed with the pipeline
        
        One of the following values:
        DISPOSITION_CONTINUE - continue to execute the pipeline
        DISPOSITION_PAUSE - wait until the status changes before executing
                            the next module
        DISPOSITION_CANCEL - stop running the pipeline
        DISPOSITION_SKIP - skip the rest of this image set
        '''
        return self.__disposition
    
    def set_disposition(self, disposition):
        self.__disposition = disposition
        event = DispositionChangedEvent(disposition)
        for listener in self.__disposition_listeners:
            listener(event)
    
    disposition = property(get_disposition, set_disposition)
    
    def add_disposition_listener(self, listener):
        self.__disposition_listeners.append(listener)

    class NoInteractionException(Exception):
        pass
    
    def load(self, filename, load_pipeline):
        '''Load a workspace from a .cpi file
        
        filename - path to file to load
        
        load_pipeline - true to load the pipeline from the file, false to
                        use the current pipeline.
        '''
        import h5py
        from .pipeline import M_PIPELINE
        import cellprofiler.measurements as cpmeas
        from cStringIO import StringIO
        
        if self.__measurements is not None:
            self.__measurements.close()
            
        self.__measurements = cpmeas.Measurements(
            filename = filename, mode = "r+")
        self.__file_list = HDF5FileList(self.measurements.hdf5_dict.hdf5_file)
        if load_pipeline and self.__measurements.has_feature(
            cpmeas.EXPERIMENT, M_PIPELINE):
            pipeline_txt = self.__measurements.get_experiment_measurement(
                M_PIPELINE).encode("utf-8")
            self.pipeline.load(StringIO(pipeline_txt))
        elif load_pipeline:
            self.pipeline.clear()
        else:
            fd = StringIO()
            self.pipeline.savetxt(fd, save_image_plane_details = False)
            self.__measurements.add_experiment_measurement(
                M_PIPELINE, fd.getvalue())
        
    def create(self, filename):
        '''Create a new workspace file
        
        filename - name of the workspace file
        '''
        from .measurements import Measurements
        if isinstance(self.measurements, Measurements):
            self.measurements.close()
        self.__measurements = Measurements(filename = filename,
                                           mode = "w")
        self.__file_list = HDF5FileList(self.measurements.hdf5_dict.hdf5_file)

class DispositionChangedEvent(object):
    def __init__(self, disposition):
        self.disposition = disposition
