# Definitional proc to organize widgets for parameters.
proc init_gui { IPINST } {
  ipgui::add_param $IPINST -name "Component_Name"
  #Adding Page
  set Page_0 [ipgui::add_page $IPINST -name "Page 0"]
  ipgui::add_param $IPINST -name "C_M_AXI_DATA_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_ADDR_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_ARUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_AWUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_BUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_CACHE_VALUE" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_DATA_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_ID_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_PROT_VALUE" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_RUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_USER_VALUE" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_WSTRB_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_INPUT_BUS_WUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_ADDR_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_BUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_CACHE_VALUE" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_DATA_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_ID_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_PROT_VALUE" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_RUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_USER_VALUE" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_OUTPUT_BUS_WUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_CACHE_VALUE" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_DATA_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_ID_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_PROT_VALUE" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_USER_VALUE" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_M_AXI_WSTRB_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_S_AXI_CONTROL_ADDR_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_S_AXI_CONTROL_DATA_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_S_AXI_CONTROL_WSTRB_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_S_AXI_DATA_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "C_S_AXI_WSTRB_WIDTH" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_pp0_stage0" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_pp1_stage0" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_pp2_stage0" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_pp3_stage0" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state1" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state54" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state55" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state56" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state57" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state58" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state59" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state60" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state61" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state62" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state66" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state67" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state68" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state69" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state73" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state76" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state77" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state78" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state79" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state80" -parent ${Page_0}
  ipgui::add_param $IPINST -name "ap_ST_fsm_state81" -parent ${Page_0}


}

proc update_PARAM_VALUE.C_M_AXI_DATA_WIDTH { PARAM_VALUE.C_M_AXI_DATA_WIDTH } {
	# Procedure called to update C_M_AXI_DATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_DATA_WIDTH { PARAM_VALUE.C_M_AXI_DATA_WIDTH } {
	# Procedure called to validate C_M_AXI_DATA_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_ADDR_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_ADDR_WIDTH } {
	# Procedure called to update C_M_AXI_INPUT_BUS_ADDR_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_ADDR_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_ADDR_WIDTH } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_ADDR_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_ARUSER_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_ARUSER_WIDTH } {
	# Procedure called to update C_M_AXI_INPUT_BUS_ARUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_ARUSER_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_ARUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_ARUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_AWUSER_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_AWUSER_WIDTH } {
	# Procedure called to update C_M_AXI_INPUT_BUS_AWUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_AWUSER_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_AWUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_AWUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_BUSER_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_BUSER_WIDTH } {
	# Procedure called to update C_M_AXI_INPUT_BUS_BUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_BUSER_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_BUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_BUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_CACHE_VALUE { PARAM_VALUE.C_M_AXI_INPUT_BUS_CACHE_VALUE } {
	# Procedure called to update C_M_AXI_INPUT_BUS_CACHE_VALUE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_CACHE_VALUE { PARAM_VALUE.C_M_AXI_INPUT_BUS_CACHE_VALUE } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_CACHE_VALUE
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_DATA_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_DATA_WIDTH } {
	# Procedure called to update C_M_AXI_INPUT_BUS_DATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_DATA_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_DATA_WIDTH } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_DATA_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_ID_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_ID_WIDTH } {
	# Procedure called to update C_M_AXI_INPUT_BUS_ID_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_ID_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_ID_WIDTH } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_ID_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_PROT_VALUE { PARAM_VALUE.C_M_AXI_INPUT_BUS_PROT_VALUE } {
	# Procedure called to update C_M_AXI_INPUT_BUS_PROT_VALUE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_PROT_VALUE { PARAM_VALUE.C_M_AXI_INPUT_BUS_PROT_VALUE } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_PROT_VALUE
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_RUSER_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_RUSER_WIDTH } {
	# Procedure called to update C_M_AXI_INPUT_BUS_RUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_RUSER_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_RUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_RUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_USER_VALUE { PARAM_VALUE.C_M_AXI_INPUT_BUS_USER_VALUE } {
	# Procedure called to update C_M_AXI_INPUT_BUS_USER_VALUE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_USER_VALUE { PARAM_VALUE.C_M_AXI_INPUT_BUS_USER_VALUE } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_USER_VALUE
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_WSTRB_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_WSTRB_WIDTH } {
	# Procedure called to update C_M_AXI_INPUT_BUS_WSTRB_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_WSTRB_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_WSTRB_WIDTH } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_WSTRB_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_INPUT_BUS_WUSER_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_WUSER_WIDTH } {
	# Procedure called to update C_M_AXI_INPUT_BUS_WUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_INPUT_BUS_WUSER_WIDTH { PARAM_VALUE.C_M_AXI_INPUT_BUS_WUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_INPUT_BUS_WUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ADDR_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ADDR_WIDTH } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_ADDR_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ADDR_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ADDR_WIDTH } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_ADDR_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_BUSER_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_BUSER_WIDTH } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_BUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_BUSER_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_BUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_BUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_CACHE_VALUE { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_CACHE_VALUE } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_CACHE_VALUE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_CACHE_VALUE { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_CACHE_VALUE } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_CACHE_VALUE
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_DATA_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_DATA_WIDTH } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_DATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_DATA_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_DATA_WIDTH } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_DATA_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ID_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ID_WIDTH } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_ID_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ID_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ID_WIDTH } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_ID_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_PROT_VALUE { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_PROT_VALUE } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_PROT_VALUE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_PROT_VALUE { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_PROT_VALUE } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_PROT_VALUE
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_RUSER_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_RUSER_WIDTH } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_RUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_RUSER_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_RUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_RUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_USER_VALUE { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_USER_VALUE } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_USER_VALUE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_USER_VALUE { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_USER_VALUE } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_USER_VALUE
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WUSER_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WUSER_WIDTH } {
	# Procedure called to update C_M_AXI_OUTPUT_BUS_WUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WUSER_WIDTH { PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_OUTPUT_BUS_WUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_CACHE_VALUE { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_CACHE_VALUE } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_CACHE_VALUE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_CACHE_VALUE { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_CACHE_VALUE } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_CACHE_VALUE
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_DATA_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_DATA_WIDTH } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_DATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_DATA_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_DATA_WIDTH } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_DATA_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ID_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ID_WIDTH } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_ID_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ID_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ID_WIDTH } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_ID_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_PROT_VALUE { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_PROT_VALUE } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_PROT_VALUE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_PROT_VALUE { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_PROT_VALUE } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_PROT_VALUE
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_USER_VALUE { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_USER_VALUE } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_USER_VALUE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_USER_VALUE { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_USER_VALUE } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_USER_VALUE
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH } {
	# Procedure called to update C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH { PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH } {
	# Procedure called to validate C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH
	return true
}

proc update_PARAM_VALUE.C_M_AXI_WSTRB_WIDTH { PARAM_VALUE.C_M_AXI_WSTRB_WIDTH } {
	# Procedure called to update C_M_AXI_WSTRB_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_WSTRB_WIDTH { PARAM_VALUE.C_M_AXI_WSTRB_WIDTH } {
	# Procedure called to validate C_M_AXI_WSTRB_WIDTH
	return true
}

proc update_PARAM_VALUE.C_S_AXI_CONTROL_ADDR_WIDTH { PARAM_VALUE.C_S_AXI_CONTROL_ADDR_WIDTH } {
	# Procedure called to update C_S_AXI_CONTROL_ADDR_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_S_AXI_CONTROL_ADDR_WIDTH { PARAM_VALUE.C_S_AXI_CONTROL_ADDR_WIDTH } {
	# Procedure called to validate C_S_AXI_CONTROL_ADDR_WIDTH
	return true
}

proc update_PARAM_VALUE.C_S_AXI_CONTROL_DATA_WIDTH { PARAM_VALUE.C_S_AXI_CONTROL_DATA_WIDTH } {
	# Procedure called to update C_S_AXI_CONTROL_DATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_S_AXI_CONTROL_DATA_WIDTH { PARAM_VALUE.C_S_AXI_CONTROL_DATA_WIDTH } {
	# Procedure called to validate C_S_AXI_CONTROL_DATA_WIDTH
	return true
}

proc update_PARAM_VALUE.C_S_AXI_CONTROL_WSTRB_WIDTH { PARAM_VALUE.C_S_AXI_CONTROL_WSTRB_WIDTH } {
	# Procedure called to update C_S_AXI_CONTROL_WSTRB_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_S_AXI_CONTROL_WSTRB_WIDTH { PARAM_VALUE.C_S_AXI_CONTROL_WSTRB_WIDTH } {
	# Procedure called to validate C_S_AXI_CONTROL_WSTRB_WIDTH
	return true
}

proc update_PARAM_VALUE.C_S_AXI_DATA_WIDTH { PARAM_VALUE.C_S_AXI_DATA_WIDTH } {
	# Procedure called to update C_S_AXI_DATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_S_AXI_DATA_WIDTH { PARAM_VALUE.C_S_AXI_DATA_WIDTH } {
	# Procedure called to validate C_S_AXI_DATA_WIDTH
	return true
}

proc update_PARAM_VALUE.C_S_AXI_WSTRB_WIDTH { PARAM_VALUE.C_S_AXI_WSTRB_WIDTH } {
	# Procedure called to update C_S_AXI_WSTRB_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_S_AXI_WSTRB_WIDTH { PARAM_VALUE.C_S_AXI_WSTRB_WIDTH } {
	# Procedure called to validate C_S_AXI_WSTRB_WIDTH
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_pp0_stage0 { PARAM_VALUE.ap_ST_fsm_pp0_stage0 } {
	# Procedure called to update ap_ST_fsm_pp0_stage0 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_pp0_stage0 { PARAM_VALUE.ap_ST_fsm_pp0_stage0 } {
	# Procedure called to validate ap_ST_fsm_pp0_stage0
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_pp1_stage0 { PARAM_VALUE.ap_ST_fsm_pp1_stage0 } {
	# Procedure called to update ap_ST_fsm_pp1_stage0 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_pp1_stage0 { PARAM_VALUE.ap_ST_fsm_pp1_stage0 } {
	# Procedure called to validate ap_ST_fsm_pp1_stage0
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_pp2_stage0 { PARAM_VALUE.ap_ST_fsm_pp2_stage0 } {
	# Procedure called to update ap_ST_fsm_pp2_stage0 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_pp2_stage0 { PARAM_VALUE.ap_ST_fsm_pp2_stage0 } {
	# Procedure called to validate ap_ST_fsm_pp2_stage0
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_pp3_stage0 { PARAM_VALUE.ap_ST_fsm_pp3_stage0 } {
	# Procedure called to update ap_ST_fsm_pp3_stage0 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_pp3_stage0 { PARAM_VALUE.ap_ST_fsm_pp3_stage0 } {
	# Procedure called to validate ap_ST_fsm_pp3_stage0
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state1 { PARAM_VALUE.ap_ST_fsm_state1 } {
	# Procedure called to update ap_ST_fsm_state1 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state1 { PARAM_VALUE.ap_ST_fsm_state1 } {
	# Procedure called to validate ap_ST_fsm_state1
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state54 { PARAM_VALUE.ap_ST_fsm_state54 } {
	# Procedure called to update ap_ST_fsm_state54 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state54 { PARAM_VALUE.ap_ST_fsm_state54 } {
	# Procedure called to validate ap_ST_fsm_state54
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state55 { PARAM_VALUE.ap_ST_fsm_state55 } {
	# Procedure called to update ap_ST_fsm_state55 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state55 { PARAM_VALUE.ap_ST_fsm_state55 } {
	# Procedure called to validate ap_ST_fsm_state55
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state56 { PARAM_VALUE.ap_ST_fsm_state56 } {
	# Procedure called to update ap_ST_fsm_state56 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state56 { PARAM_VALUE.ap_ST_fsm_state56 } {
	# Procedure called to validate ap_ST_fsm_state56
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state57 { PARAM_VALUE.ap_ST_fsm_state57 } {
	# Procedure called to update ap_ST_fsm_state57 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state57 { PARAM_VALUE.ap_ST_fsm_state57 } {
	# Procedure called to validate ap_ST_fsm_state57
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state58 { PARAM_VALUE.ap_ST_fsm_state58 } {
	# Procedure called to update ap_ST_fsm_state58 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state58 { PARAM_VALUE.ap_ST_fsm_state58 } {
	# Procedure called to validate ap_ST_fsm_state58
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state59 { PARAM_VALUE.ap_ST_fsm_state59 } {
	# Procedure called to update ap_ST_fsm_state59 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state59 { PARAM_VALUE.ap_ST_fsm_state59 } {
	# Procedure called to validate ap_ST_fsm_state59
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state60 { PARAM_VALUE.ap_ST_fsm_state60 } {
	# Procedure called to update ap_ST_fsm_state60 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state60 { PARAM_VALUE.ap_ST_fsm_state60 } {
	# Procedure called to validate ap_ST_fsm_state60
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state61 { PARAM_VALUE.ap_ST_fsm_state61 } {
	# Procedure called to update ap_ST_fsm_state61 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state61 { PARAM_VALUE.ap_ST_fsm_state61 } {
	# Procedure called to validate ap_ST_fsm_state61
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state62 { PARAM_VALUE.ap_ST_fsm_state62 } {
	# Procedure called to update ap_ST_fsm_state62 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state62 { PARAM_VALUE.ap_ST_fsm_state62 } {
	# Procedure called to validate ap_ST_fsm_state62
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state66 { PARAM_VALUE.ap_ST_fsm_state66 } {
	# Procedure called to update ap_ST_fsm_state66 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state66 { PARAM_VALUE.ap_ST_fsm_state66 } {
	# Procedure called to validate ap_ST_fsm_state66
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state67 { PARAM_VALUE.ap_ST_fsm_state67 } {
	# Procedure called to update ap_ST_fsm_state67 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state67 { PARAM_VALUE.ap_ST_fsm_state67 } {
	# Procedure called to validate ap_ST_fsm_state67
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state68 { PARAM_VALUE.ap_ST_fsm_state68 } {
	# Procedure called to update ap_ST_fsm_state68 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state68 { PARAM_VALUE.ap_ST_fsm_state68 } {
	# Procedure called to validate ap_ST_fsm_state68
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state69 { PARAM_VALUE.ap_ST_fsm_state69 } {
	# Procedure called to update ap_ST_fsm_state69 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state69 { PARAM_VALUE.ap_ST_fsm_state69 } {
	# Procedure called to validate ap_ST_fsm_state69
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state73 { PARAM_VALUE.ap_ST_fsm_state73 } {
	# Procedure called to update ap_ST_fsm_state73 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state73 { PARAM_VALUE.ap_ST_fsm_state73 } {
	# Procedure called to validate ap_ST_fsm_state73
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state76 { PARAM_VALUE.ap_ST_fsm_state76 } {
	# Procedure called to update ap_ST_fsm_state76 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state76 { PARAM_VALUE.ap_ST_fsm_state76 } {
	# Procedure called to validate ap_ST_fsm_state76
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state77 { PARAM_VALUE.ap_ST_fsm_state77 } {
	# Procedure called to update ap_ST_fsm_state77 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state77 { PARAM_VALUE.ap_ST_fsm_state77 } {
	# Procedure called to validate ap_ST_fsm_state77
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state78 { PARAM_VALUE.ap_ST_fsm_state78 } {
	# Procedure called to update ap_ST_fsm_state78 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state78 { PARAM_VALUE.ap_ST_fsm_state78 } {
	# Procedure called to validate ap_ST_fsm_state78
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state79 { PARAM_VALUE.ap_ST_fsm_state79 } {
	# Procedure called to update ap_ST_fsm_state79 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state79 { PARAM_VALUE.ap_ST_fsm_state79 } {
	# Procedure called to validate ap_ST_fsm_state79
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state80 { PARAM_VALUE.ap_ST_fsm_state80 } {
	# Procedure called to update ap_ST_fsm_state80 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state80 { PARAM_VALUE.ap_ST_fsm_state80 } {
	# Procedure called to validate ap_ST_fsm_state80
	return true
}

proc update_PARAM_VALUE.ap_ST_fsm_state81 { PARAM_VALUE.ap_ST_fsm_state81 } {
	# Procedure called to update ap_ST_fsm_state81 when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.ap_ST_fsm_state81 { PARAM_VALUE.ap_ST_fsm_state81 } {
	# Procedure called to validate ap_ST_fsm_state81
	return true
}


proc update_MODELPARAM_VALUE.ap_ST_fsm_state1 { MODELPARAM_VALUE.ap_ST_fsm_state1 PARAM_VALUE.ap_ST_fsm_state1 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state1}] ${MODELPARAM_VALUE.ap_ST_fsm_state1}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_pp0_stage0 { MODELPARAM_VALUE.ap_ST_fsm_pp0_stage0 PARAM_VALUE.ap_ST_fsm_pp0_stage0 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_pp0_stage0}] ${MODELPARAM_VALUE.ap_ST_fsm_pp0_stage0}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state54 { MODELPARAM_VALUE.ap_ST_fsm_state54 PARAM_VALUE.ap_ST_fsm_state54 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state54}] ${MODELPARAM_VALUE.ap_ST_fsm_state54}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state55 { MODELPARAM_VALUE.ap_ST_fsm_state55 PARAM_VALUE.ap_ST_fsm_state55 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state55}] ${MODELPARAM_VALUE.ap_ST_fsm_state55}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state56 { MODELPARAM_VALUE.ap_ST_fsm_state56 PARAM_VALUE.ap_ST_fsm_state56 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state56}] ${MODELPARAM_VALUE.ap_ST_fsm_state56}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state57 { MODELPARAM_VALUE.ap_ST_fsm_state57 PARAM_VALUE.ap_ST_fsm_state57 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state57}] ${MODELPARAM_VALUE.ap_ST_fsm_state57}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state58 { MODELPARAM_VALUE.ap_ST_fsm_state58 PARAM_VALUE.ap_ST_fsm_state58 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state58}] ${MODELPARAM_VALUE.ap_ST_fsm_state58}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state59 { MODELPARAM_VALUE.ap_ST_fsm_state59 PARAM_VALUE.ap_ST_fsm_state59 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state59}] ${MODELPARAM_VALUE.ap_ST_fsm_state59}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state60 { MODELPARAM_VALUE.ap_ST_fsm_state60 PARAM_VALUE.ap_ST_fsm_state60 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state60}] ${MODELPARAM_VALUE.ap_ST_fsm_state60}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state61 { MODELPARAM_VALUE.ap_ST_fsm_state61 PARAM_VALUE.ap_ST_fsm_state61 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state61}] ${MODELPARAM_VALUE.ap_ST_fsm_state61}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state62 { MODELPARAM_VALUE.ap_ST_fsm_state62 PARAM_VALUE.ap_ST_fsm_state62 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state62}] ${MODELPARAM_VALUE.ap_ST_fsm_state62}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_pp1_stage0 { MODELPARAM_VALUE.ap_ST_fsm_pp1_stage0 PARAM_VALUE.ap_ST_fsm_pp1_stage0 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_pp1_stage0}] ${MODELPARAM_VALUE.ap_ST_fsm_pp1_stage0}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state66 { MODELPARAM_VALUE.ap_ST_fsm_state66 PARAM_VALUE.ap_ST_fsm_state66 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state66}] ${MODELPARAM_VALUE.ap_ST_fsm_state66}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state67 { MODELPARAM_VALUE.ap_ST_fsm_state67 PARAM_VALUE.ap_ST_fsm_state67 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state67}] ${MODELPARAM_VALUE.ap_ST_fsm_state67}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state68 { MODELPARAM_VALUE.ap_ST_fsm_state68 PARAM_VALUE.ap_ST_fsm_state68 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state68}] ${MODELPARAM_VALUE.ap_ST_fsm_state68}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state69 { MODELPARAM_VALUE.ap_ST_fsm_state69 PARAM_VALUE.ap_ST_fsm_state69 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state69}] ${MODELPARAM_VALUE.ap_ST_fsm_state69}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_pp2_stage0 { MODELPARAM_VALUE.ap_ST_fsm_pp2_stage0 PARAM_VALUE.ap_ST_fsm_pp2_stage0 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_pp2_stage0}] ${MODELPARAM_VALUE.ap_ST_fsm_pp2_stage0}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state73 { MODELPARAM_VALUE.ap_ST_fsm_state73 PARAM_VALUE.ap_ST_fsm_state73 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state73}] ${MODELPARAM_VALUE.ap_ST_fsm_state73}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_pp3_stage0 { MODELPARAM_VALUE.ap_ST_fsm_pp3_stage0 PARAM_VALUE.ap_ST_fsm_pp3_stage0 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_pp3_stage0}] ${MODELPARAM_VALUE.ap_ST_fsm_pp3_stage0}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state76 { MODELPARAM_VALUE.ap_ST_fsm_state76 PARAM_VALUE.ap_ST_fsm_state76 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state76}] ${MODELPARAM_VALUE.ap_ST_fsm_state76}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state77 { MODELPARAM_VALUE.ap_ST_fsm_state77 PARAM_VALUE.ap_ST_fsm_state77 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state77}] ${MODELPARAM_VALUE.ap_ST_fsm_state77}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state78 { MODELPARAM_VALUE.ap_ST_fsm_state78 PARAM_VALUE.ap_ST_fsm_state78 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state78}] ${MODELPARAM_VALUE.ap_ST_fsm_state78}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state79 { MODELPARAM_VALUE.ap_ST_fsm_state79 PARAM_VALUE.ap_ST_fsm_state79 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state79}] ${MODELPARAM_VALUE.ap_ST_fsm_state79}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state80 { MODELPARAM_VALUE.ap_ST_fsm_state80 PARAM_VALUE.ap_ST_fsm_state80 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state80}] ${MODELPARAM_VALUE.ap_ST_fsm_state80}
}

proc update_MODELPARAM_VALUE.ap_ST_fsm_state81 { MODELPARAM_VALUE.ap_ST_fsm_state81 PARAM_VALUE.ap_ST_fsm_state81 } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.ap_ST_fsm_state81}] ${MODELPARAM_VALUE.ap_ST_fsm_state81}
}

proc update_MODELPARAM_VALUE.C_S_AXI_CONTROL_DATA_WIDTH { MODELPARAM_VALUE.C_S_AXI_CONTROL_DATA_WIDTH PARAM_VALUE.C_S_AXI_CONTROL_DATA_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_S_AXI_CONTROL_DATA_WIDTH}] ${MODELPARAM_VALUE.C_S_AXI_CONTROL_DATA_WIDTH}
}

proc update_MODELPARAM_VALUE.C_S_AXI_CONTROL_ADDR_WIDTH { MODELPARAM_VALUE.C_S_AXI_CONTROL_ADDR_WIDTH PARAM_VALUE.C_S_AXI_CONTROL_ADDR_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_S_AXI_CONTROL_ADDR_WIDTH}] ${MODELPARAM_VALUE.C_S_AXI_CONTROL_ADDR_WIDTH}
}

proc update_MODELPARAM_VALUE.C_S_AXI_DATA_WIDTH { MODELPARAM_VALUE.C_S_AXI_DATA_WIDTH PARAM_VALUE.C_S_AXI_DATA_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_S_AXI_DATA_WIDTH}] ${MODELPARAM_VALUE.C_S_AXI_DATA_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ID_WIDTH { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ID_WIDTH PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ID_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ID_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ID_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ADDR_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_DATA_WIDTH { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_DATA_WIDTH PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_DATA_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_DATA_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_DATA_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_AWUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_ARUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_RUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_BUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_USER_VALUE { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_USER_VALUE PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_USER_VALUE } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_USER_VALUE}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_USER_VALUE}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_PROT_VALUE { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_PROT_VALUE PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_PROT_VALUE } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_PROT_VALUE}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_PROT_VALUE}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_CACHE_VALUE { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_CACHE_VALUE PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_CACHE_VALUE } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_CACHE_VALUE}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_CACHE_VALUE}
}

proc update_MODELPARAM_VALUE.C_M_AXI_DATA_WIDTH { MODELPARAM_VALUE.C_M_AXI_DATA_WIDTH PARAM_VALUE.C_M_AXI_DATA_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_DATA_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_DATA_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_ID_WIDTH { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_ID_WIDTH PARAM_VALUE.C_M_AXI_INPUT_BUS_ID_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_ID_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_ID_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_ADDR_WIDTH { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_ADDR_WIDTH PARAM_VALUE.C_M_AXI_INPUT_BUS_ADDR_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_ADDR_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_ADDR_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_DATA_WIDTH { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_DATA_WIDTH PARAM_VALUE.C_M_AXI_INPUT_BUS_DATA_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_DATA_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_DATA_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_AWUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_AWUSER_WIDTH PARAM_VALUE.C_M_AXI_INPUT_BUS_AWUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_AWUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_AWUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_ARUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_ARUSER_WIDTH PARAM_VALUE.C_M_AXI_INPUT_BUS_ARUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_ARUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_ARUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_WUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_WUSER_WIDTH PARAM_VALUE.C_M_AXI_INPUT_BUS_WUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_WUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_WUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_RUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_RUSER_WIDTH PARAM_VALUE.C_M_AXI_INPUT_BUS_RUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_RUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_RUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_BUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_BUSER_WIDTH PARAM_VALUE.C_M_AXI_INPUT_BUS_BUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_BUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_BUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_USER_VALUE { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_USER_VALUE PARAM_VALUE.C_M_AXI_INPUT_BUS_USER_VALUE } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_USER_VALUE}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_USER_VALUE}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_PROT_VALUE { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_PROT_VALUE PARAM_VALUE.C_M_AXI_INPUT_BUS_PROT_VALUE } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_PROT_VALUE}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_PROT_VALUE}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_CACHE_VALUE { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_CACHE_VALUE PARAM_VALUE.C_M_AXI_INPUT_BUS_CACHE_VALUE } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_CACHE_VALUE}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_CACHE_VALUE}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_ID_WIDTH { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_ID_WIDTH PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ID_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ID_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_ID_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_ADDR_WIDTH { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_ADDR_WIDTH PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ADDR_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ADDR_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_ADDR_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_DATA_WIDTH { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_DATA_WIDTH PARAM_VALUE.C_M_AXI_OUTPUT_BUS_DATA_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_DATA_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_DATA_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH PARAM_VALUE.C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_AWUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_ARUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_WUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_WUSER_WIDTH PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_WUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_RUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_RUSER_WIDTH PARAM_VALUE.C_M_AXI_OUTPUT_BUS_RUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_RUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_RUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_BUSER_WIDTH { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_BUSER_WIDTH PARAM_VALUE.C_M_AXI_OUTPUT_BUS_BUSER_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_BUSER_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_BUSER_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_USER_VALUE { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_USER_VALUE PARAM_VALUE.C_M_AXI_OUTPUT_BUS_USER_VALUE } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_USER_VALUE}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_USER_VALUE}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_PROT_VALUE { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_PROT_VALUE PARAM_VALUE.C_M_AXI_OUTPUT_BUS_PROT_VALUE } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_PROT_VALUE}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_PROT_VALUE}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_CACHE_VALUE { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_CACHE_VALUE PARAM_VALUE.C_M_AXI_OUTPUT_BUS_CACHE_VALUE } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_CACHE_VALUE}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_CACHE_VALUE}
}

proc update_MODELPARAM_VALUE.C_S_AXI_CONTROL_WSTRB_WIDTH { MODELPARAM_VALUE.C_S_AXI_CONTROL_WSTRB_WIDTH PARAM_VALUE.C_S_AXI_CONTROL_WSTRB_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_S_AXI_CONTROL_WSTRB_WIDTH}] ${MODELPARAM_VALUE.C_S_AXI_CONTROL_WSTRB_WIDTH}
}

proc update_MODELPARAM_VALUE.C_S_AXI_WSTRB_WIDTH { MODELPARAM_VALUE.C_S_AXI_WSTRB_WIDTH PARAM_VALUE.C_S_AXI_WSTRB_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_S_AXI_WSTRB_WIDTH}] ${MODELPARAM_VALUE.C_S_AXI_WSTRB_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH { MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_WEIGHTS_BUS_WSTRB_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_WSTRB_WIDTH { MODELPARAM_VALUE.C_M_AXI_WSTRB_WIDTH PARAM_VALUE.C_M_AXI_WSTRB_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_WSTRB_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_WSTRB_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_WSTRB_WIDTH { MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_WSTRB_WIDTH PARAM_VALUE.C_M_AXI_INPUT_BUS_WSTRB_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_INPUT_BUS_WSTRB_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_INPUT_BUS_WSTRB_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH { MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH } {
	# Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
	set_property value [get_property value ${PARAM_VALUE.C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_OUTPUT_BUS_WSTRB_WIDTH}
}

