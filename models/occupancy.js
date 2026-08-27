const mongoose = require("mongoose");

const occupancySchema = new mongoose.Schema(
  {
    parkingLot: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "ParkingLot",
      required: true,
      index: true,
    },

    timestamp: {
      type: Date,
      required: true,
      index: true,
    },

    totalSlots: {
      type: Number,
      required: true,
    },

    occupiedSlots: {
      type: Number,
      required: true,
      min: 0,
    },

    availableSlots: {
      type: Number,
      required: true,
      min: 0,
    },

    occupancyRate: {
      type: Number,
      required: true,
      min: 0,
      max: 100,
    },

    source: {
      type: String,
      enum: ["booking", "sensor", "manual"],
      default: "booking",
    },
  },
  {
    timestamps: true,
  }
);

occupancySchema.index({
  parkingLot: 1,
  timestamp: -1,
});

module.exports = mongoose.model("Occupancy", occupancySchema);