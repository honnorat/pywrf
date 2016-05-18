#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import math
import numpy as np
import os.path

import pywrf.util.dates as pud
import pywrf.util.files as puf

from pywrf.util.misc import to_list
from pywrf.namelist import Namelist

_thisdir = os.path.dirname(__file__)
_namelist_wrf_template = os.path.join(_thisdir, "namelist.wrf_template")


def compute_eta_levels(n_levels, m0=0.7, m1=0.6, n0=-0.2, n1=-0.275):

    x = np.arange(n_levels) / float(n_levels-1)
    h00 = lambda t: 2*t*t*t-3*t*t+1
    h01 = lambda t: t*t*(3-2*t)
    h10 = lambda t: t*(t*t-2*t+1)
    h11 = lambda t: t*t*(t-1)

    fc = h01(x) + m0*h10(x) + m1*h11(x)
    eta_levs = h00(fc) + n0*h10(x) + n1*h11(x)

    return [float(e) for e in eta_levs]


def calc_time_step(dx, interval_s=3600):

    k = int(math.ceil(interval_s/(float(5*dx/1000.))))

    while interval_s/float(k)-float(interval_s/k) > 1e-12:
        k += 1

    return interval_s / k


class WRFNamelist(Namelist):

    def __init__(self, config=None, template_file=None):

        # Fetch template file for namelist
        try:
            wrf_template = puf.expand_path(config["nml_wrf_template"])
        except:
            if template_file is None:
                wrf_template = _namelist_wrf_template
            else:
                wrf_template = template_file

        super(WRFNamelist, self).__init__(config, wrf_template)

        # DFI
        self.dfi_opt = self.from_config("dfi_opt", 0)

    def calc_values(self):

        super(WRFNamelist, self).calc_values()

        nd = self.max_dom
        dx = self.from_config("dx", 27000)
        dy = self.from_config("dy", dx)
        if dx < 10:
            # dx is in degrees: get the value grabed in metgrid instead.
            dx = self.from_config("met_dx")
            dy = self.from_config("met_dy")
        dt = calc_time_step(min(dx, dy))

        # Compute accumulated grid ratio
        grid_id = list(range(1, nd+1))
        parent_grid_ratio = self.from_config("parent_grid_ratio", [1])
        parent_id = self.from_config("parent_id", list(range(len(parent_grid_ratio))))

        accumulated_gr = [1]
        for i, gr in enumerate(parent_grid_ratio[1:]):
            parent = parent_id[i+1]-1
            accumulated_gr.append(accumulated_gr[parent]*int(gr))

        # Save computed values in config for future use
        pywrf_store = self.section("pywrf_store")
        pywrf_store["parent_id"] = parent_id
        pywrf_store["accumulated_gr"] = accumulated_gr
        pywrf_store["fine_domains"]   = to_list(self.from_config("ndown/fine_domains", -1))

        # Compute default time steps for each grid
        dt_start = [ max(int(math.ceil(dt/(1.*gr))), 2) for gr in accumulated_gr ]
        dt_min = [ int(math.ceil(dts/2)) for dts in dt_start ]
        dt_max = [ int(math.ceil(dts*2)) for dts in dt_start ]

        # Compute default grid steps
        list_dx = [ dx/float(gr) for gr in accumulated_gr ]
        list_dy = [ dy/float(gr) for gr in accumulated_gr ]

        ## Section '&time_control'
        ##########
        nml_time = self.section("time_control")

        nml_time["start_year"]  = nd * [ self.date_s.year ]
        nml_time["start_month"] = nd * [ self.date_s.month]
        nml_time["start_day"]   = nd * [ self.date_s.day  ]
        nml_time["start_hour"]  = nd * [ self.date_s.hour ]
        nml_time["end_year"]    = nd * [ self.date_e.year ]
        nml_time["end_month"]   = nd * [ self.date_e.month]
        nml_time["end_day"]     = nd * [ self.date_e.day  ]
        nml_time["end_hour"]    = nd * [ self.date_e.hour ]

        nml_time["interval_seconds"]   = self.from_config("interval_seconds", 10800)
        nml_time["history_interval"]   = to_list(self.from_config("history_interval", 60), nd)
        nml_time["restart_interval"]   = self.from_config("restart_interval", 1440)
        nml_time["restart"]            = self.from_config("restart", False)
        nml_time["input_from_file"]    = to_list(self.from_config("input_from_file", True), nd)
        nml_time["frames_per_outfile"] = to_list(self.from_config("frames_per_outfile", 999999), nd)
        nml_time["fine_input_stream"]  = to_list(self.from_config("fine_input_stream", 0), nd)

        nml_time["write_hist_at_0h_rst"]    = self.from_config("write_hist_at_0h_rst", True)
        nml_time["adjust_output_times"]     = self.from_config("adjust_output_times", True)
        nml_time["ignore_iofields_warning"] = self.from_config("ignore_iofields_warning", True)
        nml_time["iofields_filename"]       = to_list(self.from_config("iofields_filename", "NONE_SPECIFIED"), nd)

        ## Section '&domains'
        ##########
        nml_domains = self.section("domains")

        nml_domains["max_dom"]           = nd
        nml_domains["dx"]                = list_dx
        nml_domains["dy"]                = list_dy
        nml_domains["grid_id"]           = grid_id
        nml_domains["parent_id"]         = parent_id
        nml_domains["parent_grid_ratio"]      = parent_grid_ratio
        nml_domains["parent_time_step_ratio"] = parent_grid_ratio

        nml_domains["i_parent_start"]    = self.from_config("i_parent_start", [1] + (nd-1)*[10])
        nml_domains["j_parent_start"]    = self.from_config("j_parent_start", [1] + (nd-1)*[10])
        nml_domains["e_we"]              = self.from_config("e_we",          [70] + (nd-1)*[88])
        nml_domains["e_sn"]              = self.from_config("e_sn",          [70] + (nd-1)*[88])

        nml_domains["num_metgrid_levels"]      = self.from_config("num_metgrid_levels")
        nml_domains["num_metgrid_soil_levels"] = self.from_config("num_metgrid_soil_levels")

        nml_domains["time_step"]               = self.from_config("time_step", dt)
        nml_domains["use_adaptive_time_step"]  = self.from_config("use_adaptive_time_step", False)
        nml_domains["starting_time_step"]      = self.from_config("starting_time_step", dt_start)
        nml_domains["min_time_step"]           = self.from_config("min_time_step", dt_min)
        nml_domains["max_time_step"]           = self.from_config("max_time_step", dt_max)
        nml_domains["max_step_increase_pct"]   = self.from_config("max_step_increase_pct", [10] + (nd-1)*[51])

        # Take care of vertical levels
        num_eta_levels = self.from_config("num_eta_levels", 41)
        eta_levels = self.from_config("eta_levels")
        if eta_levels == "spline":
            eta_levels = compute_eta_levels(num_eta_levels)

        if isinstance(eta_levels, list):
            nml_domains["e_vert"] = nd * [ len(eta_levels) ]
            nml_domains["eta_levels"] = eta_levels
        else:
            nml_domains["e_vert"] = nd * [ num_eta_levels ]

        ## Section '&dynamics'
        ##########
        nml_dynamics = self.section("dynamics")
        nml_dynamics["diff_opt"] = to_list(self.from_config("diff_opt", 1), nd)
        nml_dynamics["km_opt"]   = to_list(self.from_config("km_opt",   4), nd)
        nml_dynamics["damp_opt"] = self.from_config("damp_opt", 0)
        nml_dynamics["dampcoef"] = to_list(self.from_config("dampcoef", 0.0), nd)

        ## Section '&physics'
        ##########
        nml_physics = self.section("physics")

        mp_physics         = self.from_config("mp_physics", 3)         # Default : WSM 3-class simple ice scheme
        cu_physics         = self.from_config("cu_physics", 1)         # Default : Kain-Fritsch (new Eta) scheme
        ra_lw_physics      = self.from_config("ra_lw_physics", 1)      # Default : RRTM scheme
        ra_sw_physics      = self.from_config("ra_sw_physics", 1)      # Default : Dudhia scheme
        bl_pbl_physics     = self.from_config("bl_pbl_physics", 1)     # Default : YSU scheme
        sf_sfclay_physics  = self.from_config("sf_sfclay_physics", 1)  # Default : Revised MM5 Monin-Obukhov scheme
        sf_surface_physics = self.from_config("sf_surface_physics", 2) # Default : unified Noah land-surface model
        num_soil_layers = {     # Number of soil layers in land surface model
            0: 0,   # No LSM, zero layer
            1: 5,   # thermal diffusion scheme : 5 layers
            2: 4,   # unified Noah : 4 layers
            3: 6,   # RUC : 6 layers
            4: 4,   # Noah-MP : 4 layers
            5: 10,  # Community Land Model CLM4 : 10 layers
            7: 2,   # Pleim-Xiu scheme : 2 layers
            8: 3,   # SSBiB : 3 layers
        }
        nml_physics["mp_physics"]         = to_list(mp_physics, nd)
        nml_physics["cu_physics"]         = to_list(cu_physics, nd)
        nml_physics["ra_lw_physics"]      = to_list(ra_lw_physics, nd)
        nml_physics["ra_sw_physics"]      = to_list(ra_sw_physics, nd)
        nml_physics["bl_pbl_physics"]     = to_list(bl_pbl_physics, nd)
        nml_physics["sf_sfclay_physics"]  = to_list(sf_sfclay_physics, nd)
        nml_physics["sf_surface_physics"] = to_list(sf_surface_physics, nd)
        nml_physics["num_land_cat"]       = self.from_config("num_land_cat")
        try:
            nml_physics["num_soil_layers"] = num_soil_layers[sf_surface_physics]
        except KeyError:
            raise Exception("Unknown value of sf_surface_physics: {}".format(sf_surface_physics))

        radt = math.ceil(list_dx[-1]/1000.)
        nml_physics["radt"] = to_list(self.from_config("radt", radt), nd)
        nml_physics["cudt"] = to_list(self.from_config("cudt", 0), nd)
        nml_physics["bldt"] = to_list(self.from_config("bldt", 0), nd)

        # Diagnostics
        diagnostics = self.from_config("diagnostics", {})

        if "climate" in diagnostics:
            diag_climate = diagnostics["climate"]
            if diag_climate["activate"]:
                nml_time["output_diagnostics"] = 1
                nml_time["io_form_auxhist3"] = diag_climate.get("io_form", 2)
                nml_time["auxhist3_outname"] = diag_climate.get("outname", "wrfxtrm_d<domain>_<date>")
                nml_time["auxhist3_interval"]   = to_list(diag_climate.get("interval", 1440), nd)
                nml_time["frames_per_auxhist3"] = to_list(diag_climate.get("frames_per_file", 999999), nd)

        if "p_levels" in diagnostics:
            diag_plev = diagnostics["p_levels"]
            if diag_plev and diag_plev["activate"]:
                nml_diags = self.section("diags")
                nml_diags["p_lev_diags"] = 1
                nml_diags["press_levels"] = diag_plev.get("press_levels", [92500, 85000, 70000])
                nml_diags["num_press_levels"] = len(nml_diags["press_levels"])
                nml_diags["extrap_below_grnd"] = diag_plev.get("extrap_below_grnd", 2)
                nml_time["io_form_auxhist23"] = diag_plev.get("io_form", 2)
                nml_time["auxhist23_outname"] = diag_plev.get("outname", "wrfplev_d<domain>_<date>")
                nml_time["auxhist23_interval"]   = to_list(diag_plev.get("interval", 60), nd)
                nml_time["frames_per_auxhist23"] = to_list(diag_plev.get("frames_per_file", 999999), nd)

        if "afwa" in diagnostics:
            nml_diags = self.section("afwa")
            diag_afwa = diagnostics["afwa"]
            for diag in ( "diag", "severe", "ptype", "buoy", "therm", "icing", "vis", "cloud" ):
                diag_value = to_list(diag_afwa.get(diag, 0), nd)
                if any(diag_value[:nd]):
                    # If a diag is activated on any grid, we must activate 'afwa_diag_opt' on
                    # the corresponding grid.
                    diag_opt = copy.copy(nml_diags.get("afwa_diag_opt", diag_value))     # Required field
                    diag_opt.extend(diag_value[len(diag_opt):])  #
                    for i in range(len(diag_value)):
                        diag_opt[i] |= diag_value[i]
                    nml_diags["afwa_diag_opt"] = diag_opt
                    nml_diags["afwa_{}_opt".format(diag)] = diag_value
            if nml_diags:
                # At least one AFWA diag is activated, we have to set up the output
                nml_time["io_form_auxhist2"]  = 2
                nml_time["auxhist2_outname"]  = diag_afwa.get("outname", "wrfafwa_d<domain>_<date>")
                nml_time["auxhist2_interval"] = to_list(diag_afwa.get("interval", 60), nd)

            # The diags produce the following NetCDF variables :
            # default: WSPD10MAX    : WIND SPD MAX 10 M (m s-1)
            #          AFWA_MSLP    : Mean sea level pressure (Pa)
            #          AFWA_PWAT    : Precipitable Water (kg m-2)
            # severe : W_UP_MAX     : MAX Z-WIND UPDRAFT (m s-1)
            #          W_DN_MAX     : MAX Z-WIND DOWNDRAFT (m s-1)
            #          UP_HELI_MAX  : MAX UPDRAFT HELICITY" (m2 s-2)
            #          W_MEAN       : HOURLY MEAN Z-WIND (m s-1)
            #          TCOLI_MAX    : MAX TOTAL COLUMN INTEGRATED ICE (kg m-2)
            #          GRPL_FLX_MAX : MAX PSEUDO GRAUPEL FLUX (g kg-1 m s-1)
            #          AFWA_CAPE    : Convective Avail Pot Energy (J kg-1)
            #          AFWA_CIN     : Convective Inhibition (J kg-1)
            #          AFWA_ZLFC    : Level of Free Convection (m)
            #          AFWA_PLFC    : Pressure of LFC (Pa)
            #          AFWA_LIDX    : Surface Lifted Index (K)
            #          AFWA_HAIL    : Hail Diameter (Weibull) (mm)
            #          AFWA_LLWS    : 0-2000 ft wind shear (m s-1)
            #          AFWA_TORNADO : Tornado wind speed (Weibull) (m s-1)
            # ptype :  AFWA_TOTPRECIP:Total simulation precip (mm)
            #          AFWA_SNOW    : Liquid Equivalent Snow fall (mm)
            #          AFWA_ICE     : Ice fall (mm)
            #          AFWA_FZRA    : Freezing rain fall (mm)
            #          AFWA_SNOWFALL: Snow fall (mm)
            # icing :  FZLEV        : FREEZING LEVEL (m)
            #          ICINGTOP     : TOPMOST ICING LEVEL (m)
            #          ICINGBOT     : BOTTOMMOST ICING LEVEL (m)
            #          QICING_LG_MAX: COLUMN MAX ICING MIXING RATIO (>50 um) (kg kg-1)
            #          QICING_SM_MAX: COLUMN MAX ICING MIXING RATIO (<50 um) (kg kg-1)
            #          ICING_LG     : TOTAL COLUMN INTEGRATED ICING (>50 um) (kg m-2)
            #          ICING_SM     : TOTAL COLUMN INTEGRATED ICING (<50 um) (kg m-2)
            # buoy :   AFWA_CAPE_MU : Most unstable CAPE 0-180mb (J kg-1)
            #          AFWA_CIN_MU  : Most unstable CIN 0-180mb (J kg-1)
            # therm :  AFWA_HEATIDX : Heat index (K)
            #          AFWA_WCHILL  : Wind chill (K)
            #          AFWA_FITS    : Fighter Index of Thermal Stress (K)
            # vis :    AFWA_VIS     : Visibility at the surface (m)
            #          AFWA_VIS_DUST: Visibility at the surface due to dust (m)

        # Update namelist with extra keywords
        self.update_with_extra("namelist_wrf")

        # Specific actions for derived classes
        self.calc_other()

        # DFI
        self.calc_dfi()

    def calc_other(self):
        # Can be implemented by derived classes
        pass

    def calc_dfi(self):

        if self.dfi_opt == 0:
            return

        dfi_backward_m = self.from_config("dfi_backward_m", 0)
        dfi_foreward_m = self.from_config("dfi_foreward_m", 0)

        date_dfi_s = pud.advance_date(self.date_s, increment_m=-dfi_backward_m)
        date_dfi_e = pud.advance_date(self.date_s, increment_m=+dfi_foreward_m)

        dfi = self.section("dfi_control")
        dfi["dfi_opt"] = self.dfi_opt
        dfi["dfi_bckstop_year"]   = date_dfi_s.year
        dfi["dfi_bckstop_month"]  = date_dfi_s.month
        dfi["dfi_bckstop_day"]    = date_dfi_s.day
        dfi["dfi_bckstop_hour"]   = date_dfi_s.hour
        dfi["dfi_bckstop_minute"] = date_dfi_s.minute
        dfi["dfi_fwdstop_year"]   = date_dfi_e.year
        dfi["dfi_fwdstop_month"]  = date_dfi_e.month
        dfi["dfi_fwdstop_day"]    = date_dfi_e.day
        dfi["dfi_fwdstop_hour"]   = date_dfi_e.hour
        dfi["dfi_fwdstop_minute"] = date_dfi_e.minute


class NdownRealNamelist(WRFNamelist):

    def calc_other(self):

        pywrf_store = self.section("pywrf_store")
        list_parent_id = pywrf_store["parent_id"]
        accumulated_gr = pywrf_store["accumulated_gr"]
        fine_domains   = pywrf_store["fine_domains"]
        first_fine     = fine_domains[0]

        nml_domains = self.section("domains")
        list_i_start = nml_domains["i_parent_start"]
        list_j_start = nml_domains["j_parent_start"]
        list_e_we = nml_domains["e_we"]
        list_e_sn = nml_domains["e_sn"]
        list_dx   = nml_domains["dx"]
        list_dy   = nml_domains["dy"]

        nml_domains["max_dom"] = len(fine_domains)
        nml_domains["parent_id"] = [ list_parent_id[i-1]-list_parent_id[first_fine-1] for i in fine_domains ]
        nml_domains["parent_grid_ratio"] = [ accumulated_gr[i-1]/accumulated_gr[first_fine-1] for i in fine_domains ]
        nml_domains["i_parent_start"]    = [ list_i_start[i-1] for i in fine_domains ]
        nml_domains["j_parent_start"]    = [ list_j_start[j-1] for j in fine_domains ]
        nml_domains["e_we"] = [ list_e_we[i-1] for i in fine_domains ]
        nml_domains["e_sn"] = [ list_e_sn[j-1] for j in fine_domains ]
        nml_domains["dx"]   = [ list_dx[i-1]   for i in fine_domains ]
        nml_domains["dy"]   = [ list_dy[j-1]   for j in fine_domains ]
        nml_domains["time_step"]          = calc_time_step(nml_domains["dx"][0])
        nml_domains["starting_time_step"] = nml_domains["starting_time_step"][first_fine-1:]
        nml_domains["min_time_step"]      = nml_domains["min_time_step"][first_fine-1:]
        nml_domains["max_time_step"]      = nml_domains["max_time_step"][first_fine-1:]

        # FIXME: valid only if no FDDA otherwise we'll have to run real for the whole inner period.
        nml_time = self.section("time_control")
        nml_time["end_year"]    = self.max_dom * [ self.date_s.year ]
        nml_time["end_month"]   = self.max_dom * [ self.date_s.month]
        nml_time["end_day"]     = self.max_dom * [ self.date_s.day  ]
        nml_time["end_hour"]    = self.max_dom * [ self.date_s.hour ]


class NdownNdownNamelist(WRFNamelist):

    def calc_other(self):

        pywrf_store = self.section("pywrf_store")
        list_parent_id    = pywrf_store["parent_id"]
        fine_domains      = pywrf_store["fine_domains"]
        first_fine        = fine_domains[0]
        first_fine_parent = list_parent_id[first_fine-1]

        nml_domains = self.section("domains")
        list_e_we    = nml_domains["e_we"]
        list_e_sn    = nml_domains["e_sn"]
        list_dx      = nml_domains["dx"]
        list_dy      = nml_domains["dy"]

        if self.date_s == self.date_e:
            # Otherwise ndown will not produce wrfbdy_d02
            self.date_e = pud.advance_date(self.date_e, increment_h=1)

        nml_domains["max_dom"] = 2
        nml_domains["parent_id"] = [0, 1]
        nml_domains["parent_grid_ratio"] = [1, nml_domains["parent_grid_ratio"][first_fine-1]]
        nml_domains["i_parent_start"]    = [1, nml_domains["i_parent_start"][first_fine-1]]
        nml_domains["j_parent_start"]    = [1, nml_domains["j_parent_start"][first_fine-1]]
        nml_domains["e_we"] = [ list_e_we[i-1] for i in (first_fine_parent, first_fine) ]
        nml_domains["e_sn"] = [ list_e_sn[j-1] for j in (first_fine_parent, first_fine) ]
        nml_domains["dx"]   = [ list_dx[i-1]   for i in (first_fine_parent, first_fine) ]
        nml_domains["dy"]   = [ list_dy[j-1]   for j in (first_fine_parent, first_fine) ]

        nml_time = self.section("time_control")
        nml_time["start_year"]  = 2 * [ self.date_s.year ]
        nml_time["start_month"] = 2 * [ self.date_s.month]
        nml_time["start_day"]   = 2 * [ self.date_s.day  ]
        nml_time["start_hour"]  = 2 * [ self.date_s.hour ]
        nml_time["end_year"]    = 2 * [ self.date_e.year ]
        nml_time["end_month"]   = 2 * [ self.date_e.month]
        nml_time["end_day"]     = 2 * [ self.date_e.day  ]
        nml_time["end_hour"]    = 2 * [ self.date_e.hour ]

        nml_time["interval_seconds"] = self.from_config("ndown/interval_seconds", nml_time["interval_seconds"])


class NdownDFINamelist(NdownRealNamelist):

    def calc_other(self):

        super(NdownDFINamelist, self).calc_other()

        nd = len(self["pywrf_store"]["fine_domains"])

        # Fix tracer bug in DFI: WRF falls when tracer option is greater than 1.
        nml_dyn = self.section("dynamics")
        nml_dyn["moist_adv_opt"]    = nd * [1]
        nml_dyn["scalar_adv_opt"]   = nd * [1]
        nml_dyn["tracer_adv_opt"]   = nd * [1]
        nml_dyn["tke_adv_opt"]      = nd * [1]
        nml_dyn["momentum_adv_opt"] = nd * [1]


class NdownWRFNamelist(NdownRealNamelist):

    def calc_other(self):

        super(NdownWRFNamelist, self).calc_other()

        nd = len(self["pywrf_store"]["fine_domains"])

        # Set dates
        nml_time = self.section("time_control")
        nml_time["end_year"]    = nd * [ self.date_e.year ]
        nml_time["end_month"]   = nd * [ self.date_e.month]
        nml_time["end_day"]     = nd * [ self.date_e.day  ]
        nml_time["end_hour"]    = nd * [ self.date_e.hour ]

        nml_time["interval_seconds"] = self.from_config("ndown/interval_seconds", nml_time["interval_seconds"])
        nml_time["fine_input_stream"] = [0] + max(1, nd-1)*[2]

        # Deactivate DFI: it should have been done earlier
        self.dfi_opt = 0

if __name__ == "__main__":

    nml = WRFNamelist()
    nml.calc_values()
    #